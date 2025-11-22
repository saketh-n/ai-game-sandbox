# Caching Feature Documentation

## 🎯 Overview

The caching system stores generated asset prompts to save time and API costs by avoiding regenerating the same prompts. When you enter a game theme that's already been generated, the result is instantly retrieved from cache instead of calling Claude API again.

## 🏗️ Architecture

### Backend Components

#### 1. **Cache Manager** (`cache_manager.py`)
- Manages persistent JSON-based cache storage
- Stores prompts with their generated results and timestamps
- Provides methods for CRUD operations on cached data

#### 2. **API Endpoints**

**POST `/generate-asset-prompts`** (Enhanced)
- Checks cache before calling Claude API
- If found: Returns cached result instantly (marked as `cached: true`)
- If not found: Generates new result, caches it, returns it
- Response includes `cached` boolean flag

**GET `/cached-prompts`**
- Returns list of all cached prompts with metadata
- Called on frontend load to show available cached prompts
- Response format:
```json
{
  "prompts": [
    {
      "prompt": "Full prompt text",
      "timestamp": "2024-01-15T10:30:00",
      "preview": "First 100 chars..."
    }
  ],
  "count": 5
}
```

**POST `/fetch-cached-prompt`**
- Fetches the complete generated result for a specific cached prompt
- Used when user clicks on a cached prompt from the list
- Request body: `{ "prompt": "exact prompt text" }`
- Response:
```json
{
  "prompt": "Full prompt text",
  "result": "Complete JSON response",
  "timestamp": "2024-01-15T10:30:00"
}
```

**DELETE `/cache/{prompt}`**
- Deletes a specific cached prompt
- Returns 404 if prompt not found

**DELETE `/cache`**
- Clears entire cache
- Nuclear option for cache management

### Frontend Components

#### State Management
```typescript
const [cachedPrompts, setCachedPrompts] = useState<CachedPrompt[]>([])
const [showCachedPrompts, setShowCachedPrompts] = useState(false)
const [isCached, setIsCached] = useState(false)
```

#### Functions

**`fetchCachedPrompts()`**
- Called on component mount (`useEffect`)
- Fetches list of cached prompts from backend
- Automatically shows cached prompts section if any exist

**`loadCachedPrompt(cachedPrompt)`**
- Called when user clicks a cached prompt
- Fetches full result from backend
- Displays the asset prompts immediately (no Claude API call)
- Shows "Loaded from cache (instant!)" indicator

**`generateAssetPrompts(userPrompt)`** (Enhanced)
- Generates new prompts (may hit cache on backend)
- Refreshes cached prompts list after generation
- Updates `isCached` flag based on backend response

## 🎨 UI/UX Features

### Cached Prompts Display

**Location**: Between header and input box

**Features**:
- 📋 Shows list of recent prompts (newest first)
- 🕒 Displays timestamp for each cached prompt
- 👀 Preview text (first 100 characters)
- 🎭 Hover effects for interactivity
- 📜 Scrollable list (max height 240px)
- 🔄 Hide/Show toggle button

**States**:
1. **Hidden** - Collapsed button showing count
2. **Visible** - Expanded list of cached prompts
3. **None** - No cached prompts (nothing shown)

### Visual Indicators

**Cache Hit Badge**:
```
✓ Loaded from cache (instant!)
```
- Green checkmark icon
- Shown below input box when result was cached
- Disappears when generating new prompts

## 📁 File Storage

### Cache File: `prompt_cache.json`

**Location**: `backend/prompt_cache.json`

**Format**:
```json
{
  "cyberpunk noir detective game": {
    "result": "{...complete JSON response...}",
    "timestamp": "2024-01-15T10:30:00.123456"
  },
  "fantasy medieval RPG with dragons": {
    "result": "{...complete JSON response...}",
    "timestamp": "2024-01-15T11:45:00.789012"
  }
}
```

**Git**: Excluded via `.gitignore` (cache is local only)

## 🚀 Performance Benefits

### Time Savings
- **Without cache**: 5-15 seconds (Claude API call)
- **With cache**: < 1 second (instant retrieval)
- **Savings**: ~90-95% reduction in response time

### Cost Savings
- **API calls**: Reduced by number of cache hits
- **Token usage**: Zero tokens for cached responses
- Especially valuable for repeated testing/development

## 🔧 Technical Details

### Cache Key Strategy
- **Key**: Exact prompt text (case-sensitive)
- **Why**: Simple, deterministic, works perfectly for exact matches
- **Trade-off**: Similar prompts won't match (e.g., "RPG game" vs "rpg game")

### Data Flow

#### First Generation:
```
User Input → Backend → Check Cache → Miss → Claude API → Generate → Cache → Return
                                                                        ↓
                                                                    Save to JSON
```

#### Cached Generation:
```
User Input → Backend → Check Cache → Hit → Return (instant!)
```

#### Loading Cached Prompt:
```
User Click → fetch-cached-prompt → Read from Cache → Return → Display
```

### Cache Invalidation
- **Never expires**: Cache persists indefinitely
- **Manual clearing**: Use DELETE `/cache` endpoint
- **Per-prompt deletion**: Use DELETE `/cache/{prompt}` endpoint
- **File deletion**: Delete `prompt_cache.json` manually

## 🎮 Usage Examples

### Example 1: First Time Generation
```
1. User enters: "cyberpunk noir detective game"
2. Backend checks cache → Not found
3. Calls Claude API (5-10 seconds)
4. Caches result
5. Returns to frontend
6. Shows normal result
```

### Example 2: Repeated Generation
```
1. User enters: "cyberpunk noir detective game" (same as before)
2. Backend checks cache → Found!
3. Returns cached result (instant)
4. Frontend shows: "✓ Loaded from cache (instant!)"
```

### Example 3: Loading from History
```
1. User opens app
2. Frontend fetches cached prompts
3. Shows list: "You have 5 cached prompts"
4. User clicks: "cyberpunk noir detective game"
5. Instantly loads full asset prompts
6. Shows: "✓ Loaded from cache (instant!)"
```

## 🛠️ Development Notes

### Adding New Cache Features

**To add cache expiration**:
```python
# In cache_manager.py
from datetime import datetime, timedelta

def is_expired(self, prompt: str, max_age_days: int = 7) -> bool:
    if prompt not in self.cache_data:
        return True
    
    timestamp = datetime.fromisoformat(self.cache_data[prompt]['timestamp'])
    age = datetime.now() - timestamp
    return age > timedelta(days=max_age_days)
```

**To add fuzzy matching**:
```python
# Use difflib for similar prompts
from difflib import get_close_matches

def find_similar(self, prompt: str, threshold: float = 0.9):
    matches = get_close_matches(prompt, self.cache_data.keys(), n=1, cutoff=threshold)
    return self.get(matches[0]) if matches else None
```

### Testing Cache

```bash
# Test cache hit
curl -X POST http://localhost:8000/generate-asset-prompts \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test game"}'

# Repeat - should be instant
curl -X POST http://localhost:8000/generate-asset-prompts \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test game"}'

# List cached prompts
curl http://localhost:8000/cached-prompts

# Fetch specific cached prompt
curl -X POST http://localhost:8000/fetch-cached-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test game"}'

# Clear cache
curl -X DELETE http://localhost:8000/cache
```

## 📊 Monitoring

### Check cache status:
```python
from cache_manager import cache

print(f"Total cached prompts: {len(cache.cache_data)}")
print(f"Cache file size: {os.path.getsize('prompt_cache.json')} bytes")
```

### View cache contents:
```bash
cat backend/prompt_cache.json | jq
```

## 🔐 Security Considerations

- ✅ Cache stored locally (not in git)
- ✅ No sensitive data in prompts (user-provided only)
- ✅ File permissions respect OS defaults
- ⚠️ No encryption (not needed for game prompts)
- ⚠️ No user authentication (single-user dev tool)

## 🎯 Future Enhancements

- [ ] Cache statistics dashboard
- [ ] Cache size limits (auto-cleanup when full)
- [ ] Export/import cache
- [ ] Share cache between team members
- [ ] Search cached prompts
- [ ] Tag/categorize cached prompts
- [ ] Cache hit rate metrics
- [ ] Prompt similarity search

---

**Implementation Date**: November 2024  
**Status**: ✅ Complete and Working

