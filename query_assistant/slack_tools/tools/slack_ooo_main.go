package main

import (
	"bytes"
	"crypto/md5"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/slack-go/slack"
)

type UserInfo struct {
	Name        string `json:"name"`
	RealName    string `json:"real_name"`
	DisplayName string `json:"display_name"`
}

type MessageData struct {
	Message     string `json:"message"`
	Timestamp   string `json:"timestamp"`
	UserID      string `json:"user_id"`
	UserName    string `json:"user_name"`
	MessageDate string `json:"message_date"`
}

type DateExtraction struct {
	DeclaredOOODate []string `json:"declared_ooo_date"`
	Reason          string   `json:"reason"`
}

type BatchDateExtraction struct {
	Results []struct {
		MessageIndex    int      `json:"message_index"`
		DeclaredOOODate []string `json:"declared_ooo_date"`
		Reason          string   `json:"reason"`
	} `json:"results"`
}

type OOODeclaration struct {
	UserName           string   `json:"user_name"`
	DeclaredOOODate    []string `json:"declared_ooo_date"`
	DateMessageWasSent string   `json:"date_message_was_sent"`
	RawMessage         string   `json:"raw_message"`
	Reason             string   `json:"reason"`
}

type OOOResult struct {
	Success         bool             `json:"success"`
	Today           string           `json:"today"`
	OOODeclarations []OOODeclaration `json:"ooo_declarations"`
	Error           string           `json:"error,omitempty"`
}

type LLMRequest struct {
	Messages    []LLMMessage `json:"messages"`
	Model       string       `json:"model"`
	MaxTokens   int          `json:"max_tokens"`
	Temperature float64      `json:"temperature"`
	TopP        float64      `json:"top_p"`
	User        string       `json:"user"`
	Stream      bool         `json:"stream"`
}

type LLMMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type LLMResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

var (
	userCache      = make(map[string]UserInfo)
	userCacheMutex = sync.RWMutex{}
	responseCache  = make(map[string]DateExtraction)
	cacheMutex     = sync.RWMutex{}
	httpClient     *http.Client
	llmSemaphore   chan struct{}
)

func init() {
	// Optimized HTTP client with connection pooling and keep-alive
	transport := &http.Transport{
		MaxIdleConns:        100,
		MaxIdleConnsPerHost: 20,
		IdleConnTimeout:     90 * time.Second,
		DisableKeepAlives:   false,
	}

	httpClient = &http.Client{
		Transport: transport,
		Timeout:   15 * time.Second, // Increased for batch processing
	}

	// Limit concurrent LLM calls to prevent rate limiting
	maxLLMConcurrency := 10
	if envVal := os.Getenv("MAX_LLM_CONCURRENCY"); envVal != "" {
		if val, err := strconv.Atoi(envVal); err == nil && val > 0 {
			maxLLMConcurrency = val
		}
	}
	llmSemaphore = make(chan struct{}, maxLLMConcurrency)
}

func main() {
	token := os.Getenv("SLACK_API_TOKEN")
	if token == "" {
		result := OOOResult{Success: false, Error: "SLACK_API_TOKEN is not set"}
		output, _ := json.Marshal(result)
		fmt.Println(string(output))
		os.Exit(1)
	}

	// Get argument names from environment
	argNames := []string{"channel", "oldest"}
	args := make(map[string]string)
	for _, arg := range argNames {
		if val := os.Getenv(arg); val != "" {
			args[arg] = val
		}
	}

	result := executeSlackAction(token, args)
	output, _ := json.Marshal(result)
	fmt.Println(string(output))
}

func executeSlackAction(token string, args map[string]string) OOOResult {
	// Use Eastern Time Zone for proper date calculation
	loc, err := time.LoadLocation("America/New_York")
	if err != nil {
		log.Printf("Warning: Could not load Eastern timezone, using UTC: %v", err)
		loc = time.UTC
	}

	currentTime := time.Now().In(loc)
	today := currentTime.Format("2006-01-02")

	log.Printf("Starting Slack OOO analysis at: %s", currentTime.Format("2006-01-02 15:04:05 MST"))
	fmt.Printf("Current date and time (Eastern): %s\n", currentTime.Format("2006-01-02 15:04:05 MST"))
	fmt.Printf("Using today date for analysis: %s\n", today)

	api := slack.New(token)

	channel := args["channel"]
	if channel == "" {
		return OOOResult{Success: false, Error: "Channel parameter is required"}
	}

	oldest := args["oldest"]
	if oldest == "" {
		oldest = "24h"
	}

	channelID, err := findChannel(api, channel)
	if err != nil {
		return OOOResult{Success: false, Error: fmt.Sprintf("Channel not found: %s", channel)}
	}

	oldestTimestamp, err := processTimeFilter(oldest)
	if err != nil {
		return OOOResult{Success: false, Error: fmt.Sprintf("Invalid time filter: %s", err)}
	}

	log.Printf("Fetching messages from channel %s since %s", channelID, oldestTimestamp)

	messages, err := getChannelMessages(api, channelID, oldestTimestamp)
	if err != nil {
		return OOOResult{Success: false, Error: fmt.Sprintf("Error fetching messages: %s", err)}
	}

	if len(messages) == 0 {
		return OOOResult{
			Success:         true,
			Today:           today,
			OOODeclarations: []OOODeclaration{},
		}
	}

	log.Printf("Found %d messages to analyze for OOO date extraction", len(messages))

	declarations := extractOOODatesFromMessages(messages, today)

	log.Printf("Analysis complete. Found %d OOO declarations", len(declarations))

	return OOOResult{
		Success:         true,
		Today:           today,
		OOODeclarations: declarations,
	}
}

func findChannel(api *slack.Client, channelInput string) (string, error) {
	log.Printf("Attempting to find channel: %s", channelInput)

	if channelInput == "" {
		return "", fmt.Errorf("channel input is empty")
	}

	if strings.HasPrefix(channelInput, "C") && len(channelInput) == 11 {
		log.Printf("Using provided channel ID directly: %s", channelInput)
		return channelInput, nil
	}

	channelInput = strings.TrimPrefix(channelInput, "#")

	channels, _, err := api.GetConversations(&slack.GetConversationsParameters{
		Types: []string{"public_channel", "private_channel"},
	})
	if err != nil {
		return "", err
	}

	for _, channel := range channels {
		if strings.EqualFold(channel.Name, channelInput) {
			log.Printf("Exact match found: %s", channel.ID)
			return channel.ID, nil
		}
	}

	return "", fmt.Errorf("channel not found: %s", channelInput)
}

func processTimeFilter(oldestParam string) (string, error) {
	if oldestParam == "" {
		return "", fmt.Errorf("oldest parameter is empty")
	}

	if matched, _ := regexp.MatchString(`^\d+(\.\d+)?$`, oldestParam); matched {
		return oldestParam, nil
	}

	re := regexp.MustCompile(`^(\d+)([hdmw])$`)
	matches := re.FindStringSubmatch(strings.ToLower(oldestParam))
	if len(matches) != 3 {
		return "", fmt.Errorf("invalid time format")
	}

	amount, _ := strconv.Atoi(matches[1])
	unit := matches[2]

	var seconds int
	switch unit {
	case "h":
		seconds = 3600 * amount
	case "d":
		seconds = 86400 * amount
	case "w":
		seconds = 604800 * amount
	case "m":
		seconds = 60 * amount
	default:
		return "", fmt.Errorf("unsupported time unit")
	}

	targetTime := time.Now().Unix() - int64(seconds)
	return fmt.Sprintf("%.6f", float64(targetTime)), nil
}

func getUserInfo(api *slack.Client, userID string) UserInfo {
	if userID == "" {
		return UserInfo{Name: "Unknown User", RealName: "Unknown User", DisplayName: "Unknown User"}
	}

	userCacheMutex.RLock()
	if cached, exists := userCache[userID]; exists {
		userCacheMutex.RUnlock()
		return cached
	}
	userCacheMutex.RUnlock()

	user, err := api.GetUserInfo(userID)
	if err != nil {
		log.Printf("Could not retrieve user info for %s: %s", userID, err)
		userInfo := UserInfo{Name: "Unknown User", RealName: "Unknown User", DisplayName: "Unknown User"}

		userCacheMutex.Lock()
		userCache[userID] = userInfo
		userCacheMutex.Unlock()

		return userInfo
	}

	displayName := user.Profile.DisplayName
	if displayName == "" {
		displayName = user.RealName
		if displayName == "" {
			displayName = user.Name
		}
	}

	userInfo := UserInfo{
		Name:        user.Name,
		RealName:    user.RealName,
		DisplayName: displayName,
	}

	userCacheMutex.Lock()
	userCache[userID] = userInfo
	userCacheMutex.Unlock()

	return userInfo
}

func getChannelMessages(api *slack.Client, channelID, oldest string) ([]MessageData, error) {
	var allMessages []MessageData
	var cursor string

	for {
		params := &slack.GetConversationHistoryParameters{
			ChannelID: channelID,
			Oldest:    oldest,
			Limit:     200,
			Cursor:    cursor,
		}

		history, err := api.GetConversationHistory(params)
		if err != nil {
			return nil, err
		}

		if len(history.Messages) == 0 {
			break
		}

		messageChan := make(chan MessageData, len(history.Messages)*2)
		var wg sync.WaitGroup

		for _, msg := range history.Messages {
			wg.Add(1)
			go func(m slack.Message) {
				defer wg.Done()

				userInfo := getUserInfo(api, m.User)

				messageDate := "Unknown Date"
				if m.Timestamp != "" {
					if ts, err := strconv.ParseFloat(m.Timestamp, 64); err == nil {
						messageDate = time.Unix(int64(ts), 0).Format("2006-01-02")
					}
				}

				processedMsg := MessageData{
					Message:     m.Text,
					Timestamp:   m.Timestamp,
					UserID:      m.User,
					UserName:    userInfo.DisplayName,
					MessageDate: messageDate,
				}

				messageChan <- processedMsg

				if m.ThreadTimestamp != "" && m.ThreadTimestamp == m.Timestamp {
					replies, _, _, err := api.GetConversationReplies(&slack.GetConversationRepliesParameters{
						ChannelID: channelID,
						Timestamp: m.ThreadTimestamp,
					})
					if err == nil && len(replies) > 1 {
						for _, reply := range replies[1:] {
							replyUserInfo := getUserInfo(api, reply.User)
							replyDate := "Unknown Date"
							if reply.Timestamp != "" {
								if ts, err := strconv.ParseFloat(reply.Timestamp, 64); err == nil {
									replyDate = time.Unix(int64(ts), 0).Format("2006-01-02")
								}
							}

							replyMsg := MessageData{
								Message:     reply.Text,
								Timestamp:   reply.Timestamp,
								UserID:      reply.User,
								UserName:    replyUserInfo.DisplayName,
								MessageDate: replyDate,
							}

							messageChan <- replyMsg
						}
					}
				}
			}(msg)
		}

		go func() {
			wg.Wait()
			close(messageChan)
		}()

		for msg := range messageChan {
			allMessages = append(allMessages, msg)
		}

		if !history.HasMore {
			break
		}
		cursor = history.ResponseMetaData.NextCursor
	}

	log.Printf("Total messages retrieved: %d", len(allMessages))
	return allMessages, nil
}

func extractOOODatesFromMessages(messages []MessageData, today string) []OOODeclaration {
	// Process messages in optimized batches for LLM efficiency
	const batchSize = 8 // Increased batch size since we're doing simpler date extraction

	var allDeclarations []OOODeclaration
	var declarationsMutex sync.Mutex
	var wg sync.WaitGroup

	// Process messages in batches
	for i := 0; i < len(messages); i += batchSize {
		end := i + batchSize
		if end > len(messages) {
			end = len(messages)
		}

		batch := messages[i:end]

		// Filter out empty messages before sending to LLM
		var validMessages []MessageData
		for _, msg := range batch {
			if strings.TrimSpace(msg.Message) != "" {
				validMessages = append(validMessages, msg)
			}
		}

		if len(validMessages) == 0 {
			continue
		}

		wg.Add(1)
		go func(msgBatch []MessageData, batchIndex int) {
			defer wg.Done()

			log.Printf("Processing batch %d: %d messages", batchIndex+1, len(msgBatch))

			// Extract dates from batch
			batchDeclarations := processBatchForDateExtraction(msgBatch, today)

			declarationsMutex.Lock()
			allDeclarations = append(allDeclarations, batchDeclarations...)
			declarationsMutex.Unlock()
		}(validMessages, i/batchSize)
	}

	wg.Wait()

	// Deduplicate declarations
	declarationMap := make(map[string]*OOODeclaration)
	for _, declaration := range allDeclarations {
		key := fmt.Sprintf("%s_%s_%s_%s", declaration.UserName, declaration.DateMessageWasSent, declaration.RawMessage, declaration.Reason)
		if existing, exists := declarationMap[key]; exists {
			dateSet := make(map[string]bool)
			for _, date := range existing.DeclaredOOODate {
				dateSet[date] = true
			}
			for _, date := range declaration.DeclaredOOODate {
				dateSet[date] = true
			}

			var mergedDates []string
			for date := range dateSet {
				mergedDates = append(mergedDates, date)
			}
			sort.Strings(mergedDates)
			existing.DeclaredOOODate = mergedDates
		} else {
			declarationMap[key] = &declaration
		}
	}

	var finalDeclarations []OOODeclaration
	for _, declaration := range declarationMap {
		finalDeclarations = append(finalDeclarations, *declaration)
	}

	sort.Slice(finalDeclarations, func(i, j int) bool {
		return finalDeclarations[i].DateMessageWasSent < finalDeclarations[j].DateMessageWasSent
	})

	return finalDeclarations
}

func processBatchForDateExtraction(messages []MessageData, today string) []OOODeclaration {
	var declarations []OOODeclaration

	// Try batch processing first (more efficient)
	if len(messages) > 1 {
		if batchResults := tryBatchDateExtraction(messages, today); len(batchResults) > 0 {
			return batchResults
		}
		log.Printf("Batch date extraction failed, falling back to individual analysis")
	}

	// Fallback to individual processing if batch fails
	const maxConcurrency = 5 // Higher concurrency since we're doing simpler processing
	semaphore := make(chan struct{}, maxConcurrency)
	resultChan := make(chan *OOODeclaration, len(messages))
	var wg sync.WaitGroup

	for _, message := range messages {
		wg.Add(1)
		go func(msg MessageData) {
			defer wg.Done()

			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			dateExtraction := extractDatesWithLLM(msg, today)

			// Since we know every message is OOO, create declaration if we got any dates
			if len(dateExtraction.DeclaredOOODate) > 0 {
				declaration := &OOODeclaration{
					UserName:           msg.UserName,
					DeclaredOOODate:    dateExtraction.DeclaredOOODate,
					DateMessageWasSent: msg.MessageDate,
					RawMessage:         msg.Message,
					Reason:             dateExtraction.Reason,
				}
				resultChan <- declaration
			} else {
				// If LLM couldn't extract dates, use message date as fallback
				declaration := &OOODeclaration{
					UserName:           msg.UserName,
					DeclaredOOODate:    []string{msg.MessageDate},
					DateMessageWasSent: msg.MessageDate,
					RawMessage:         msg.Message,
					Reason:             "Could not extract OOO dates from message.",
				}
				resultChan <- declaration
			}
		}(message)
	}

	go func() {
		wg.Wait()
		close(resultChan)
	}()

	for declaration := range resultChan {
		declarations = append(declarations, *declaration)
	}

	return declarations
}

func tryBatchDateExtraction(messages []MessageData, today string) []OOODeclaration {
	// Acquire semaphore for rate limiting
	llmSemaphore <- struct{}{}
	defer func() { <-llmSemaphore }()

	// Create optimized prompt focused purely on date extraction
	var promptBuilder strings.Builder
	promptBuilder.WriteString("Extract the out-of-office dates from these messages. Each message is an OOO declaration - focus on finding the specific dates they will be out and provide a brief reason.\n\n")
	promptBuilder.WriteString("Respond with valid JSON only:\n")
	promptBuilder.WriteString(`{"results": [{"message_index": 0, "declared_ooo_date": ["2024-07-25", "2024-07-26"], "reason": "sick leave"}]}`)
	promptBuilder.WriteString("\n\nMessages to analyze:\n")

	for i, msg := range messages {
		promptBuilder.WriteString(fmt.Sprintf("Message %d:\n", i))
		promptBuilder.WriteString(fmt.Sprintf("User: %s | Posted: %s\n", msg.UserName, msg.MessageDate))
		promptBuilder.WriteString(fmt.Sprintf("Message: \"%s\"\n\n", msg.Message))
	}

	promptBuilder.WriteString(fmt.Sprintf("Today's date: %s\n", today))
	promptBuilder.WriteString("Extract all declared OOO dates and provide a brief reason (e.g., 'vacation', 'sick day', 'appointment', 'family emergency'). Resolve relative dates like 'today', 'tomorrow', 'Monday' based on when each message was posted.")

	result := makeLLMRequest(promptBuilder.String())
	if result == "" {
		return []OOODeclaration{}
	}

	var batchExtraction BatchDateExtraction
	if err := json.Unmarshal([]byte(result), &batchExtraction); err != nil {
		log.Printf("Failed to parse batch date extraction response: %v", err)
		return []OOODeclaration{}
	}

	var declarations []OOODeclaration
	for _, result := range batchExtraction.Results {
		if result.MessageIndex < len(messages) {
			msg := messages[result.MessageIndex]

			// Use extracted dates or fallback to message date
			oooDate := result.DeclaredOOODate
			if len(oooDate) == 0 {
				oooDate = []string{msg.MessageDate}
			}

			// Use extracted reason or provide default
			reason := result.Reason
			if reason == "" {
				reason = "Out of office"
			}

			declarations = append(declarations, OOODeclaration{
				UserName:           msg.UserName,
				DeclaredOOODate:    oooDate,
				DateMessageWasSent: msg.MessageDate,
				RawMessage:         msg.Message,
				Reason:             reason,
			})
		}
	}

	log.Printf("Batch date extraction processed %d messages, created %d declarations", len(messages), len(declarations))
	return declarations
}

func extractDatesWithLLM(messageData MessageData, today string) DateExtraction {
	// Check cache first - include username to prevent collisions
	cacheKey := generateCacheKey(messageData.Message, messageData.MessageDate, today, messageData.UserName)

	cacheMutex.RLock()
	if cached, exists := responseCache[cacheKey]; exists {
		cacheMutex.RUnlock()
		return cached
	}
	cacheMutex.RUnlock()

	// Acquire semaphore for rate limiting
	llmSemaphore <- struct{}{}
	defer func() { <-llmSemaphore }()

	// Simplified prompt focused on date extraction with reason
	prompt := fmt.Sprintf(`Extract OOO dates from this message and provide a brief reason. Respond with JSON only:
{"declared_ooo_date": ["2024-07-25", "2024-07-26"], "reason": "sick day"}

User: %s | Posted: %s | Today: %s
Message: "%s"

Extract all declared OOO dates and provide a brief reason (e.g., 'vacation', 'sick day', 'appointment', 'family emergency'). Convert relative dates like 'today', 'tomorrow', 'Monday' to YYYY-MM-DD format based on the posted date.`,
		messageData.UserName, messageData.MessageDate, today, messageData.Message)

	content := makeLLMRequest(prompt)
	if content == "" {
		return DateExtraction{DeclaredOOODate: []string{}, Reason: ""}
	}

	var extraction DateExtraction
	if err := json.Unmarshal([]byte(content), &extraction); err != nil {
		log.Printf("Failed to parse date extraction response: %v", err)
		return DateExtraction{DeclaredOOODate: []string{}, Reason: ""}
	}

	// Provide default reason if none extracted
	if extraction.Reason == "" {
		extraction.Reason = "Out of office"
	}

	// Cache the result
	cacheMutex.Lock()
	responseCache[cacheKey] = extraction
	cacheMutex.Unlock()

	return extraction
}

func makeLLMRequest(prompt string) string {
	baseURL := os.Getenv("LLM_BASE_URL")
	apiKey := os.Getenv("LLM_API_KEY")

	if baseURL == "" || apiKey == "" {
		log.Printf("Missing LLM configuration - baseURL: %s, apiKey present: %v", baseURL, apiKey != "")
		return ""
	}

	llmRequest := LLMRequest{
		Messages: []LLMMessage{
			{Role: "system", Content: "You are a date extraction specialist. Extract out-of-office dates from messages. Always respond with valid JSON only."},
			{Role: "user", Content: prompt},
		},
		Model:       "openai/Llama-4-Scout",
		MaxTokens:   250, // Increased slightly since we're extracting dates + reasons
		Temperature: 0.1,
		TopP:        0.1,
		User:        os.Getenv("KUBIYA_USER_EMAIL"),
		Stream:      false,
	}

	jsonData, err := json.Marshal(llmRequest)
	if err != nil {
		log.Printf("Failed to marshal LLM request: %v", err)
		return ""
	}

	req, err := http.NewRequest("POST", baseURL+"/v1/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Printf("Failed to create HTTP request: %v", err)
		return ""
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := httpClient.Do(req)
	if err != nil {
		log.Printf("HTTP request failed: %v", err)
		return ""
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		log.Printf("LLM API returned status %d", resp.StatusCode)
		return ""
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read response body: %v", err)
		return ""
	}

	var llmResponse LLMResponse
	if err := json.Unmarshal(body, &llmResponse); err != nil {
		log.Printf("Failed to parse LLM response JSON: %v", err)
		return ""
	}

	if len(llmResponse.Choices) == 0 {
		log.Printf("No choices in LLM response")
		return ""
	}

	return strings.TrimSpace(llmResponse.Choices[0].Message.Content)
}

func generateCacheKey(message, messageDate, today, userName string) string {
	data := fmt.Sprintf("%s|%s|%s|%s", message, messageDate, today, userName)
	hash := md5.Sum([]byte(data))
	return fmt.Sprintf("%x", hash)
}
