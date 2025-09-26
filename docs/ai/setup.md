# Local LLM Setup

Complete guide for setting up local Large Language Model inference with ParquetFrame using Ollama. Maintain privacy and control while getting AI-powered data insights.

## Overview

ParquetFrame uses [Ollama](https://ollama.ai/) for local LLM inference, ensuring your data and queries never leave your machine. This setup guide covers installation, model selection, and optimization for the best AI query experience.

## Why Local LLM?

- **Privacy First**: Your data never leaves your machine
- **No API Costs**: No per-query charges or rate limits
- **Always Available**: Works offline once set up
- **Customizable**: Fine-tune models for your specific domain
- **Enterprise Ready**: Meets strict data governance requirements

## Prerequisites

- **System Requirements**:
  - 8GB RAM minimum (16GB+ recommended)
  - 10GB+ free disk space for models
  - Modern CPU (Apple Silicon, Intel, or AMD)
  - Optional: NVIDIA GPU for faster inference

- **Supported Platforms**:
  - macOS 10.15+
  - Linux (Ubuntu, CentOS, etc.)
  - Windows 10/11 with WSL2

## Installation

### Step 1: Install Ollama

#### macOS
```bash
# Option 1: Homebrew (recommended)
brew install ollama

# Option 2: Direct download
# Visit https://ollama.ai/download and download the macOS installer
```

#### Linux
```bash
# Official installer (recommended)
curl -fsSL https://ollama.ai/install.sh | sh

# Or manual installation
wget https://ollama.ai/download/linux-amd64
chmod +x linux-amd64
sudo mv linux-amd64 /usr/local/bin/ollama
```

#### Windows
1. Install WSL2 if not already installed:
   ```powershell
   wsl --install
   ```

2. In WSL2 Ubuntu, run the Linux installation:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

### Step 2: Start Ollama Service

```bash
# Start Ollama server
ollama serve

# The service will start on http://localhost:11434
# Keep this terminal open or run as a background service
```

### Step 3: Install ParquetFrame with AI Support

```bash
# Install ParquetFrame with AI dependencies
pip install parquetframe[ai]

# Or install everything
pip install parquetframe[all]
```

## Model Selection and Installation

### Recommended Models for Data Analysis

#### 1. CodeLlama (Best for SQL)
```bash
# Install CodeLlama 7B (recommended for most users)
ollama pull codellama:7b

# For more powerful systems
ollama pull codellama:13b
ollama pull codellama:34b  # Requires 32GB+ RAM
```

**Pros**: Specifically trained for code generation, excellent SQL output
**Cons**: Larger models require more resources
**Best for**: Complex SQL queries, data transformations

#### 2. Llama 3.2 (Best General Purpose)
```bash
# Install Llama 3.2 3B (efficient)
ollama pull llama3.2:3b

# Install Llama 3.2 1B (very fast)
ollama pull llama3.2:1b
```

**Pros**: Fast inference, good general reasoning
**Cons**: Sometimes less precise for complex SQL
**Best for**: Quick data exploration, simple queries

#### 3. Mistral (Good Balance)
```bash
# Install Mistral 7B
ollama pull mistral:7b
```

**Pros**: Good balance of performance and accuracy
**Cons**: May require more prompting for domain-specific queries
**Best for**: Business intelligence queries, mixed workloads

### Model Comparison

| Model | Size | RAM Needed | Speed | SQL Quality | Best Use Case |
|-------|------|------------|-------|-------------|---------------|
| llama3.2:1b | 1.3GB | 4GB | ⚡⚡⚡ | ⭐⭐ | Quick exploration |
| llama3.2:3b | 2.0GB | 6GB | ⚡⚡ | ⭐⭐⭐ | General purpose |
| codellama:7b | 3.8GB | 8GB | ⚡ | ⭐⭐⭐⭐ | Complex SQL |
| mistral:7b | 4.1GB | 8GB | ⚡ | ⭐⭐⭐ | Business queries |
| codellama:13b | 7.3GB | 16GB | 🐌 | ⭐⭐⭐⭐⭐ | Production use |

## Configuration and Testing

### Verify Installation

```python
# Test ParquetFrame AI integration
import asyncio
from parquetframe.ai import LLMAgent

async def test_setup():
    try:
        agent = LLMAgent(model_name="llama3.2:3b")
        print("✅ AI agent created successfully")

        # Test with simple data
        import pandas as pd
        test_df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['NYC', 'LA', 'Chicago']
        })

        result = await agent.generate_query(
            "Show me all people over 25",
            test_df
        )

        if result.success:
            print("✅ Query generation working")
            print(f"Generated SQL: {result.query}")
        else:
            print("❌ Query generation failed")
            print(f"Error: {result.error}")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("Check that Ollama is running: ollama serve")

# Run the test
asyncio.run(test_setup())
```

### Check Available Models

```bash
# List installed models
ollama list

# Example output:
NAME                ID              SIZE      MODIFIED
codellama:7b        8fdf8f752f6e    3.8 GB    2 hours ago
llama3.2:3b         a6990ed6be41    2.0 GB    1 day ago
```

```python
# Check from Python
from parquetframe.ai import LLMAgent

agent = LLMAgent()
available_models = agent.get_available_models()
print("Available models:", available_models)
```

## Performance Optimization

### System Optimization

#### Memory Management
```bash
# Check system memory
free -h  # Linux
top      # macOS/Linux

# Ollama will automatically manage model loading
# But you can control concurrency:
export OLLAMA_NUM_PARALLEL=2  # Limit parallel requests
```

#### GPU Acceleration (NVIDIA)
```bash
# Install CUDA toolkit (Linux)
sudo apt install nvidia-cuda-toolkit

# Ollama will automatically use GPU if available
nvidia-smi  # Check GPU status
```

#### Apple Silicon Optimization
```bash
# Ollama automatically uses Metal on Apple Silicon
# No additional configuration needed
# Check Activity Monitor for GPU usage
```

### Model-Specific Configuration

```python
# Optimize for speed (production)
fast_agent = LLMAgent(
    model_name="llama3.2:1b",
    temperature=0.0,        # Deterministic
    max_retries=1,          # Fast failure
    use_multi_step=False    # Skip complex reasoning
)

# Optimize for accuracy (analysis)
accurate_agent = LLMAgent(
    model_name="codellama:13b",
    temperature=0.1,        # Slightly creative
    max_retries=3,          # More attempts
    use_multi_step=True     # Better for complex queries
)

# Balance speed and quality
balanced_agent = LLMAgent(
    model_name="codellama:7b",
    temperature=0.1,
    max_retries=2
)
```

## Advanced Configuration

### Custom Model Parameters

```bash
# Run model with custom parameters
ollama run codellama:7b

# In the Ollama prompt:
/set parameter temperature 0.1
/set parameter top_p 0.9
/set parameter num_ctx 4096  # Context length
```

### Environment Variables

```bash
# Ollama configuration
export OLLAMA_HOST=0.0.0.0:11434  # Allow remote connections
export OLLAMA_MODELS=/custom/path  # Custom model storage
export OLLAMA_NUM_PARALLEL=4       # Concurrent requests
export OLLAMA_MAX_LOADED_MODELS=3  # Memory management

# ParquetFrame AI configuration
export PARQUETFRAME_AI_MODEL=codellama:7b
export PARQUETFRAME_AI_TIMEOUT=30
```

### Running as a System Service

#### Linux (systemd)
```bash
# Create service file
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Server
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
```

#### macOS (launchd)
```bash
# Create launch agent
mkdir -p ~/Library/LaunchAgents

tee ~/Library/LaunchAgents/ai.ollama.plist > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.ollama</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load the service
launchctl load ~/Library/LaunchAgents/ai.ollama.plist
```

## Security Considerations

### Network Security

```bash
# Ollama runs on localhost by default
# For production, consider:

# 1. Firewall rules
sudo ufw deny 11434  # Block external access

# 2. Reverse proxy with authentication
# Use nginx/Apache with basic auth

# 3. VPN access only
# Configure Ollama to bind to VPN interface only
```

### Data Security

- **Local Processing**: All data stays on your machine
- **No Telemetry**: Ollama doesn't send usage data
- **Audit Logs**: Enable logging for compliance

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# All queries and responses are logged locally
# Check ~/.parquetframe/logs/ for audit trail
```

### Model Security

```bash
# Verify model checksums
ollama show codellama:7b

# Models are downloaded over HTTPS
# Stored locally in ~/.ollama/models/
```

## Troubleshooting

### Common Issues

#### 1. "Connection refused"
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start if not running
ollama serve

# Check port binding
netstat -tulpn | grep 11434
```

#### 2. "Model not found"
```bash
# List available models
ollama list

# Pull the required model
ollama pull llama3.2:3b
```

#### 3. "Out of memory"
```bash
# Check system memory
free -h

# Try a smaller model
ollama pull llama3.2:1b

# Or close other applications
```

#### 4. "Slow inference"
```python
# Use faster model
agent = LLMAgent(model_name="llama3.2:1b")

# Reduce context length
agent = LLMAgent(temperature=0.0, max_retries=1)
```

### Logs and Debugging

```bash
# Ollama logs
journalctl -u ollama -f  # Linux
tail -f /var/log/ollama.log

# ParquetFrame AI logs
export PYTHONPATH=/path/to/parquetframe
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### Performance Monitoring

```python
# Monitor query performance
import time
from parquetframe.ai import LLMAgent

agent = LLMAgent()

async def monitor_performance():
    start_time = time.time()
    result = await agent.generate_query("SELECT COUNT(*) FROM df", data)
    end_time = time.time()

    print(f"Total time: {end_time - start_time:.2f}s")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
    print(f"Generation time: {(end_time - start_time) * 1000 - result.execution_time_ms:.2f}ms")
```

## Best Practices

### Production Deployment

1. **Resource Planning**
   - Monitor memory usage patterns
   - Plan for peak concurrent queries
   - Consider model swapping for different workloads

2. **Model Management**
   - Keep multiple models for different use cases
   - Regularly update models for better performance
   - Test new models before switching production

3. **Monitoring**
   - Set up health checks for Ollama service
   - Monitor query success rates
   - Track performance metrics

### Development Workflow

```python
# Development configuration
dev_agent = LLMAgent(
    model_name="llama3.2:1b",  # Fast for testing
    temperature=0.2,           # Some creativity
    max_retries=1              # Fast failure
)

# Production configuration
prod_agent = LLMAgent(
    model_name="codellama:7b", # Better quality
    temperature=0.1,           # More deterministic
    max_retries=3              # More resilient
)
```

## Next Steps

1. **[Natural Language Queries](queries.md)** - Start using AI queries
2. **[Prompt Engineering](prompts.md)** - Improve query quality
3. **[Interactive CLI](../cli/interactive.md)** - Use AI in terminal

## Related Documentation

- [AI Features Overview](../ai-features.md)
- [Natural Language Queries](queries.md)
- [Prompt Engineering](prompts.md)
- [Interactive CLI Mode](../cli/interactive.md)
