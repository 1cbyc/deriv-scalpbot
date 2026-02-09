# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in Deriv ScalpBot, please report it responsibly.

**DO NOT** open a public issue for security vulnerabilities.

### How to Report

1. Email the maintainer directly (check GitHub profile)
2. Or use GitHub's "Report a security vulnerability" feature
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Response Time**: Within 48 hours
- **Updates**: Every 7 days until resolved
- **Credit**: Security researchers will be acknowledged (if desired)

## Security Best Practices

### For Users

#### 1. API Credentials

- ✅ **Use DEMO account** for testing (VRTC accounts)
- ✅ **Store credentials securely** in `.env` file
- ✅ **Never commit `.env`** to version control
- ✅ **Rotate API tokens** monthly
- ✅ **Enable 2FA** on Deriv account
- ✅ **Use minimal permissions** (Trading + Read only)

#### 2. Environment Setup

```bash
# Verify .env is gitignored
git status | grep ".env"
# Should return nothing

# Check for exposed secrets
git log --all --full-history -- ".env"
# Should be empty

# Scan for hardcoded credentials
git grep -i "token\|password\|secret"
# Should only show variable names
```

#### 3. API Token Permissions

When creating API token at https://api.deriv.com/dashboard:

**Required permissions:**
- ✅ Read
- ✅ Trading

**NOT required (disable these):**
- ❌ Payments
- ❌ Admin
- ❌ Transfer

#### 4. Running the Bot

- Start with **low stake amounts** ($0.50 - $1.00)
- Set **daily loss limits** to protect capital
- **Monitor logs** regularly for suspicious activity
- Use **DEMO account** until strategies are proven
- Never share your `.env` file or API credentials

### For Developers

#### 1. Code Security

- Never log API tokens or credentials
- Use environment variables for all secrets
- Validate all user inputs
- Sanitize data before logging
- Use secure WebSocket connections (WSS)

#### 2. Dependencies

```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
```

#### 3. Before Committing

```bash
# Always run pre-commit checks
git diff --cached | grep -i "token\|password\|secret\|api_key"

# Verify .env not staged
git status | grep ".env"

# Run tests
python test_system.py
```

## Known Security Considerations

### API Rate Limits

Deriv API has rate limits. The bot includes:
- Request throttling
- Exponential backoff on errors
- Connection pooling

### WebSocket Security

- Uses secure WSS connections
- Automatic reconnection with backoff
- Token refresh handling
- Connection timeout protection

### Data Privacy

- **Logs**: No credentials logged
- **Telegram**: Only trade data sent (no tokens)
- **Performance tracking**: Local only (not transmitted)

## Credential Exposure

### If You Exposed Credentials

**Immediately:**

1. **Revoke API token** at https://api.deriv.com/dashboard
2. **Generate new token** with minimal permissions
3. **Update `.env`** file with new credentials
4. **Check account activity** for unauthorized trades
5. **Enable 2FA** if not already enabled

### If Committed to Git

```bash
# Remove from history (be careful!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if repository is private!)
git push origin --force --all

# Still regenerate credentials!
```

**Better approach:** Delete repository and recreate with clean history.

## Environment File Security

### .env File Protection

The `.env` file should:
- ✅ Be in `.gitignore`
- ✅ Have restricted permissions (600)
- ✅ Never be shared or committed
- ✅ Be backed up securely offline

```bash
# Set secure permissions
chmod 600 .env

# Verify not tracked
git check-ignore .env
# Should output: .env
```

### .env.example Template

Always use `.env.example` with placeholder values:

```bash
# Good (placeholder)
DERIV_API_TOKEN=your_api_token_here

# Bad (real token)
DERIV_API_TOKEN=1kmQi3oTVfGG0rG
```

## Telegram Bot Security

### Bot Token Protection

- Never share bot token publicly
- Regenerate token if exposed (talk to @BotFather)
- Use specific chat ID (not broadcast to all)
- Monitor bot activity regularly

### Testing Bot Security

```bash
# Verify bot is private
curl https://api.telegram.org/bot<TOKEN>/getMe
# Should only work with correct token

# Check bot permissions
# Bot should only send messages, not receive commands
```

## Monitoring

### Watch for:

- Unexpected trades
- API rate limit errors
- Connection failures
- Unauthorized access attempts
- Unusual profit/loss patterns

### Enable Alerts

```bash
# In .env
ENABLE_TRADE_ALERTS=true
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Compliance

### Trading Regulations

- Check local regulations for algorithmic trading
- Ensure compliance with financial laws
- Understand tax implications
- Consult legal/financial advisor if needed

### Deriv Terms of Service

- Read: https://deriv.com/terms-and-conditions
- Comply with API usage policies
- Respect rate limits
- No market manipulation

## Security Updates

This project follows [Semantic Versioning](https://semver.org/):

- **Major.Minor.Patch** (e.g., 1.0.0)
- Security patches released as PATCH updates
- Subscribe to releases for notifications

## Additional Resources

- [Deriv API Security](https://api.deriv.com/docs/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://docs.python.org/3/library/security_warnings.html)

---

**Last Updated**: February 9, 2026  
**Contact**: See [GitHub profile](https://github.com/1cbyc) for security contact

---

<div align="center">

**🔒 Security is everyone's responsibility 🔒**

Report vulnerabilities responsibly • Never share credentials • Trade safely

</div>
