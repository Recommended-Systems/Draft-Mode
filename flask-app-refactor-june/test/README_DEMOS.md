# Demo Files Guide

## Which Demo File Should I Use?

### ✅ Recommended: `diff_demo_standalone.html`

**Use this one!** It has all code and test data embedded - completely self-contained.

**How to open:**
1. Double-click the file (opens in your default browser)
2. Or run: `open diff_demo_standalone.html`

**Advantages:**
- ✅ No CORS errors
- ✅ No server needed
- ✅ No external files required
- ✅ Works with `file://` protocol
- ✅ All diff code embedded (~700 lines)
- ✅ All test data embedded
- ✅ Instant loading

**Fixed in latest version:** The improved-diff.js code is now embedded directly in the HTML, eliminating the file loading issue.

---

### ⚠️ Advanced: `diff_demo.html`

This version loads test files from the `diff_samples/` directory using fetch.

**Requires:**
- A local web server (browsers block `file://` fetch requests)

**How to use:**
```bash
cd /Users/roman/Documents/GitHub/Draft-Mode/flask-app-refactor-june/test
python -m http.server 8000
```

Then open: `http://localhost:8000/diff_demo.html`

**Use this if:**
- You're already running the Flask app
- You want to test loading external files
- You're developing additional test cases

---

### 📊 Algorithm Comparison: `diff_evaluation.html`

Compares 6 different diff algorithms side-by-side.

**Note:** This requires CDN access (uses external libraries via `<script>` tags), so you need an internet connection.

**How to use:**
Same as `diff_demo.html` - needs a local server:
```bash
cd /Users/roman/Documents/GitHub/Draft-Mode/flask-app-refactor-june/test
python -m http.server 8000
```

Then open: `http://localhost:8000/diff_evaluation.html`

---

## Quick Reference

| File | Works Offline? | Server Required? | Best For |
|------|---------------|------------------|----------|
| **diff_demo_standalone.html** | ✅ Yes | ❌ No | Quick testing |
| diff_demo.html | ✅ Yes | ⚠️ Yes | Development |
| diff_evaluation.html | ❌ No (needs CDN) | ⚠️ Yes | Algorithm comparison |

---

## Troubleshooting CORS Errors

If you see errors like:
```
Access to fetch at 'file://...' has been blocked by CORS policy
```

**Solution 1 (Easiest):**
Use `diff_demo_standalone.html` instead

**Solution 2 (For Development):**
Start a local server:
```bash
python -m http.server 8000
```

**Why this happens:**
Browsers block JavaScript from loading local files via `fetch()` for security reasons. The standalone version embeds the data directly, avoiding this issue.

---

## Recommended Workflow

1. **Quick Test**: Open `diff_demo_standalone.html` (double-click)
2. **Detailed Analysis**: Use all three test cases in the standalone demo
3. **Integration**: Follow QUICK_START.md to integrate into Flask app
4. **Advanced**: If developing new features, use local server + `diff_demo.html`

---

## Need Help?

- Check `/test/QUICK_START.md` for integration steps
- See `/test/DIFF_SYSTEM_README.md` for complete documentation
- Review `/test/diff_samples/README.md` for test case details
