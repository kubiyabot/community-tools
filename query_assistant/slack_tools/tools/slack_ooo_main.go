package main

import (
	"bytes"
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

type OOOAnalysis struct {
	IsOOOMessage    bool     `json:"is_ooo_message"`
	DeclaredOOODate []string `json:"declared_ooo_date"`
	Reason          string   `json:"reason"`
	Confidence      string   `json:"confidence"`
}

type OOODeclaration struct {
	UserName           string   `json:"user_name"`
	DeclaredOOODate    []string `json:"declared_ooo_date"`
	DateMessageWasSent string   `json:"date_message_was_sent"`
	RawMessage         string   `json:"raw_message"`
	Today              string   `json:"today"`
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
	httpClient     = &http.Client{Timeout: 5 * time.Second} // Reduced from 30s to 5s
	llmAvailable   = true                                   // Track if LLM is working
	llmCheckMutex  = sync.RWMutex{}

	// Progress tracking
	progressStartTime time.Time
	progressTicker    *time.Ticker
	progressDone      chan bool
	progressMutex     sync.Mutex
	totalMessages     int
	processedBatches  int
)

func main() {
	// Redirect log output to stderr so it doesn't interfere with JSON output
	log.SetOutput(os.Stderr)

	token := os.Getenv("SLACK_API_TOKEN")
	if token == "" {
		// Use Eastern Time Zone for proper date calculation
		loc, err := time.LoadLocation("America/New_York")
		if err != nil {
			loc = time.UTC
		}
		currentTime := time.Now().In(loc)
		today := currentTime.Format("2006-01-02")

		result := OOOResult{Success: false, Today: today, Error: "SLACK_API_TOKEN is not set"}
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

	// Sleep before output to prevent platform duplication bug
	time.Sleep(1 * time.Second)
	fmt.Println(string(output))
	// Sleep after output to prevent platform duplication bug
	time.Sleep(1 * time.Second)
}

func startProgressIndicator(messageCount int) {
	progressMutex.Lock()
	progressStartTime = time.Now()
	totalMessages = messageCount
	processedBatches = 0
	progressDone = make(chan bool)
	progressTicker = time.NewTicker(20 * time.Second)
	progressMutex.Unlock()

	go func() {
		defer progressTicker.Stop()
		for {
			select {
			case <-progressTicker.C:
				progressMutex.Lock()
				elapsed := time.Since(progressStartTime)
				fmt.Fprintf(os.Stderr, "⏳ Still processing... %d messages analyzed in %v\n", totalMessages, elapsed.Round(time.Second))
				progressMutex.Unlock()
			case <-progressDone:
				return
			}
		}
	}()
}

func stopProgressIndicator() {
	progressMutex.Lock()
	if progressDone != nil {
		close(progressDone)
		progressDone = nil
	}
	if progressTicker != nil {
		progressTicker.Stop()
		progressTicker = nil
	}
	progressMutex.Unlock()
}

func executeSlackAction(token string, args map[string]string) OOOResult {
	// Use Eastern Time Zone for proper date calculation
	loc, err := time.LoadLocation("America/New_York")
	if err != nil {
		loc = time.UTC
	}

	currentTime := time.Now().In(loc)
	today := currentTime.Format("2006-01-02")

	api := slack.New(token)

	channel := args["channel"]
	if channel == "" {
		return OOOResult{Success: false, Today: today, Error: "Channel parameter is required"}
	}

	oldest := args["oldest"]
	if oldest == "" {
		oldest = "24h"
	}

	channelID, err := findChannel(api, channel)
	if err != nil {
		return OOOResult{Success: false, Today: today, Error: fmt.Sprintf("Channel not found: %s", channel)}
	}

	oldestTimestamp, err := processTimeFilter(oldest)
	if err != nil {
		return OOOResult{Success: false, Today: today, Error: fmt.Sprintf("Invalid time filter: %s", err)}
	}

	messages, err := getChannelMessages(api, channelID, oldestTimestamp)
	if err != nil {
		return OOOResult{Success: false, Today: today, Error: fmt.Sprintf("Error fetching messages: %s", err)}
	}

	if len(messages) == 0 {
		return OOOResult{
			Success:         true,
			Today:           today,
			OOODeclarations: []OOODeclaration{},
		}
	}

	// Start progress indicator
	fmt.Fprintf(os.Stderr, "🔍 Starting analysis of %d messages...\n", len(messages))
	startProgressIndicator(len(messages))

	declarations := analyzeMessagesForOOO(messages, today)

	// Stop progress indicator
	stopProgressIndicator()
	fmt.Fprintf(os.Stderr, "✅ Analysis complete. Found %d OOO declarations.\n", len(declarations))

	return OOOResult{
		Success:         true,
		Today:           today,
		OOODeclarations: declarations,
	}
}

func findChannel(api *slack.Client, channelInput string) (string, error) {
	if channelInput == "" {
		return "", fmt.Errorf("channel input is empty")
	}

	if strings.HasPrefix(channelInput, "C") && len(channelInput) == 11 {
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

	return allMessages, nil
}

func analyzeMessagesForOOO(messages []MessageData, today string) []OOODeclaration {
	const maxConcurrency = 25 // Increased from 10 to 25 for better performance
	const batchSize = 10      // Process 10 messages per LLM call (increased from 5)

	// Group messages into batches of 10
	var batches [][]MessageData
	for i := 0; i < len(messages); i += batchSize {
		end := i + batchSize
		if end > len(messages) {
			end = len(messages)
		}
		batch := messages[i:end]
		// Filter out empty messages
		var validMessages []MessageData
		for _, msg := range batch {
			if strings.TrimSpace(msg.Message) != "" {
				validMessages = append(validMessages, msg)
			}
		}
		if len(validMessages) > 0 {
			batches = append(batches, validMessages)
		}
	}

	semaphore := make(chan struct{}, maxConcurrency)
	resultChan := make(chan *OOODeclaration, len(messages))
	var wg sync.WaitGroup

	for batchIndex, batch := range batches {
		wg.Add(1)
		go func(messageBatch []MessageData, bIndex int) {
			defer wg.Done()

			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			analyses := fastAnalyzeMessageBatchForOOO(messageBatch, today)

			// Process each analysis result
			for i, analysis := range analyses {
				if i >= len(messageBatch) {
					break // Safety check
				}

				msg := messageBatch[i]

				if analysis.IsOOOMessage && len(analysis.DeclaredOOODate) > 0 {
					declaration := &OOODeclaration{
						UserName:           msg.UserName,
						DeclaredOOODate:    analysis.DeclaredOOODate,
						DateMessageWasSent: msg.MessageDate,
						RawMessage:         msg.Message,
						Today:              today,
					}
					resultChan <- declaration
				}
			}
		}(batch, batchIndex)
	}

	go func() {
		wg.Wait()
		close(resultChan)
	}()

	declarationMap := make(map[string]*OOODeclaration)

	for declaration := range resultChan {
		key := fmt.Sprintf("%s_%s_%s", declaration.UserName, declaration.DateMessageWasSent, declaration.RawMessage)
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
			declarationMap[key] = declaration
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

func fastAnalyzeMessageBatchForOOO(messages []MessageData, today string) []OOOAnalysis {
	// Check if LLM is available, if not, skip directly to pattern analysis
	llmCheckMutex.RLock()
	isLLMAvailable := llmAvailable
	llmCheckMutex.RUnlock()

	// If LLM has been failing, skip it entirely for performance
	if !isLLMAvailable {
		var results []OOOAnalysis
		for _, msg := range messages {
			results = append(results, patternBasedAnalysis(msg, today))
		}
		return results
	}

	// Try LLM batch analysis
	llmResults := tryLLMAnalysisBatch(messages, today)

	// If LLM failed, disable it and fallback to pattern analysis
	if len(llmResults) == 0 || (len(llmResults) > 0 && strings.Contains(llmResults[0].Reason, "LLM API error")) {
		llmCheckMutex.Lock()
		llmAvailable = false
		llmCheckMutex.Unlock()

		var results []OOOAnalysis
		for _, msg := range messages {
			results = append(results, patternBasedAnalysis(msg, today))
		}
		return results
	}

	// If we got results but not enough, fill with pattern analysis
	if len(llmResults) < len(messages) {
		for i := len(llmResults); i < len(messages); i++ {
			llmResults = append(llmResults, patternBasedAnalysis(messages[i], today))
		}
	}

	return llmResults
}

func tryLLMAnalysisBatch(messages []MessageData, today string) []OOOAnalysis {
	// Build the batch prompt
	var messageInputs []string
	for i, msg := range messages {
		messageInput := fmt.Sprintf(`Message %d:
User: %s
Date message was sent: %s
Message: "%s"`, i+1, msg.UserName, msg.MessageDate, msg.Message)
		messageInputs = append(messageInputs, messageInput)
	}

	prompt := fmt.Sprintf(`You are an expert assistant for extracting out-of-office (OOO) information from Slack messages.

Given multiple messages with user names, dates they posted, and today's date, identify whether each user is indicating they will be out of office. If they are, return a list of the specific date(s) they are expected to be out for each message.

Always resolve relative dates (like "tomorrow" or "next Friday") based on date_message_was_sent. Assume users are in the same year unless otherwise stated.

Respond ONLY with valid JSON array in this exact format (no additional text):
[
  {
    "is_ooo_message": true,
    "declared_ooo_date": ["2024-07-25", "2024-07-26"],
    "reason": "Brief explanation of why this is/isn't an OOO message",
    "confidence": "high"
  },
  {
    "is_ooo_message": false,
    "declared_ooo_date": [],
    "reason": "Brief explanation of why this is/isn't an OOO message", 
    "confidence": "high"
  }
]

### Input:
Today's date: %s

%s`, today, strings.Join(messageInputs, "\n\n"))

	llmRequest := LLMRequest{
		Messages: []LLMMessage{
			{Role: "system", Content: "You are a specialized assistant for extracting out-of-office information from Slack messages. Always respond with valid JSON array only."},
			{Role: "user", Content: prompt},
		},
		Model:       "openai/Llama-4-Scout",
		MaxTokens:   3072, // Increased for larger batch processing (10 messages)
		Temperature: 0.1,
		TopP:        0.1,
		User:        os.Getenv("KUBIYA_USER_EMAIL"),
		Stream:      false,
	}

	jsonData, err := json.Marshal(llmRequest)
	if err != nil {
		return []OOOAnalysis{}
	}

	baseURL := os.Getenv("LLM_BASE_URL")
	apiKey := os.Getenv("LLM_API_KEY")

	if baseURL == "" || apiKey == "" {
		return []OOOAnalysis{}
	}

	req, err := http.NewRequest("POST", baseURL+"/v1/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return []OOOAnalysis{}
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := httpClient.Do(req)
	if err != nil {
		return []OOOAnalysis{}
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return []OOOAnalysis{
			{IsOOOMessage: false, Reason: fmt.Sprintf("LLM API error: %d", resp.StatusCode), Confidence: "low"},
		}
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return []OOOAnalysis{}
	}

	var llmResponse LLMResponse
	if err := json.Unmarshal(body, &llmResponse); err != nil {
		return []OOOAnalysis{}
	}

	if len(llmResponse.Choices) == 0 {
		return []OOOAnalysis{}
	}

	content := strings.TrimSpace(llmResponse.Choices[0].Message.Content)

	var analyses []OOOAnalysis
	if err := json.Unmarshal([]byte(content), &analyses); err != nil {
		return []OOOAnalysis{}
	}

	return analyses
}

func fastAnalyzeMessageForOOO(messageData MessageData, today string) OOOAnalysis {
	// This function is kept for backward compatibility but now just calls the batch version
	results := fastAnalyzeMessageBatchForOOO([]MessageData{messageData}, today)
	if len(results) > 0 {
		return results[0]
	}
	return patternBasedAnalysis(messageData, today)
}

func patternBasedAnalysis(messageData MessageData, today string) OOOAnalysis {
	message := strings.ToLower(messageData.Message)

	// Define OOO patterns
	oooPatterns := []string{
		"ooo", "out of office", "be off", "be out", "taking off", "day off",
		"sick leave", "vacation", "be away", "offline", "afk", "away from",
		"taking the day", "not feeling well", "stepping out", "be unavailable",
		"holiday", "appointment", "doctor", "emergency", "family matter",
	}

	// Check if message contains OOO patterns
	hasOOOPattern := false
	for _, pattern := range oooPatterns {
		if strings.Contains(message, pattern) {
			hasOOOPattern = true
			break
		}
	}

	if !hasOOOPattern {
		return OOOAnalysis{IsOOOMessage: false, Reason: "No OOO patterns detected", Confidence: "medium"}
	}

	// Simple date extraction - look for common date patterns
	var detectedDates []string

	// Look for "today", "tomorrow", etc.
	if strings.Contains(message, "today") || strings.Contains(message, "rest of the day") {
		detectedDates = append(detectedDates, messageData.MessageDate)
	}

	if strings.Contains(message, "tomorrow") {
		// Add one day to message date
		if msgDate, err := time.Parse("2006-01-02", messageData.MessageDate); err == nil {
			tomorrow := msgDate.AddDate(0, 0, 1)
			detectedDates = append(detectedDates, tomorrow.Format("2006-01-02"))
		}
	}

	// Look for specific date patterns like "7/24", "07/25", etc.
	dateRegex := regexp.MustCompile(`\b(\d{1,2})[/-](\d{1,2})\b`)
	matches := dateRegex.FindAllStringSubmatch(message, -1)
	for _, match := range matches {
		if len(match) == 3 {
			month := match[1]
			day := match[2]
			// Assume current year and pad with zeros
			if len(month) == 1 {
				month = "0" + month
			}
			if len(day) == 1 {
				day = "0" + day
			}
			// Extract year from today's date
			todayDate, _ := time.Parse("2006-01-02", today)
			year := todayDate.Year()
			dateStr := fmt.Sprintf("%d-%s-%s", year, month, day)
			detectedDates = append(detectedDates, dateStr)
		}
	}

	// If no specific dates found, use message date as fallback
	if len(detectedDates) == 0 {
		detectedDates = append(detectedDates, messageData.MessageDate)
	}

	return OOOAnalysis{
		IsOOOMessage:    true,
		DeclaredOOODate: detectedDates,
		Reason:          "Pattern-based detection (LLM unavailable)",
		Confidence:      "medium",
	}
}
