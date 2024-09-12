FROM argoproj/argocd:latest

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

CMD ["python3", "-m", "argocd_tools"]