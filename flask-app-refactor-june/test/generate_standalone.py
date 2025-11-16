#!/usr/bin/env python3
"""
Generate standalone diff demo with embedded code and test data
"""

import os
import json

# Read the improved-diff.js file
with open('../static/js/improved-diff.js', 'r') as f:
    diff_js = f.read()

# Read test samples
test_samples = {}
for test_name in ['technical', 'creative', 'documentation']:
    with open(f'diff_samples/{test_name}_v1.md', 'r') as f:
        v1 = f.read()
    with open(f'diff_samples/{test_name}_v2.md', 'r') as f:
        v2 = f.read()
    test_samples[test_name] = {'v1': v1, 'v2': v2}

# Create the HTML template
html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diff Demo - Standalone</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            margin-bottom: 20px;
            color: #58a6ff;
        }

        .controls {
            background: #161b22;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }

        .control-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }

        select, button {
            padding: 8px 12px;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #c9d1d9;
            cursor: pointer;
            font-size: 14px;
        }

        select {
            width: 100%;
            max-width: 400px;
        }

        button {
            background: #238636;
            border-color: #238636;
            font-weight: 600;
            margin-top: 10px;
        }

        button:hover {
            background: #2ea043;
        }

        .checkbox-group {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }

        .checkbox-group label {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 0;
            font-weight: normal;
        }

        input[type="checkbox"] {
            width: 16px;
            height: 16px;
        }

        #diffContainer {
            display: none;
        }

        .stats-container {
            background: #161b22;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stat-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .stat-dot.added { background: #3fb950; }
        .stat-dot.removed { background: #f85149; }
        .stat-dot.modified { background: #d29922; }
        .stat-dot.moved { background: #58a6ff; }

        .diff-panels {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .diff-panel {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: auto;
            max-height: 600px;
        }

        .panel-header {
            background: #161b22;
            padding: 10px 15px;
            border-bottom: 1px solid #30363d;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .panel-content {
            padding: 10px;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.5;
        }

        .diff-line {
            display: flex;
            padding: 2px 0;
            border-left: 4px solid transparent;
        }

        .line-number {
            min-width: 50px;
            padding: 0 10px;
            color: #6e7681;
            text-align: right;
            user-select: none;
            flex-shrink: 0;
        }

        .line-content {
            flex: 1;
            padding-right: 10px;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .diff-unchanged {
            background: transparent;
        }

        .diff-added {
            background: rgba(63, 185, 80, 0.15);
            border-left-color: #3fb950;
        }

        .diff-removed {
            background: rgba(248, 81, 73, 0.15);
            border-left-color: #f85149;
        }

        .diff-modified {
            background: rgba(210, 153, 34, 0.15);
            border-left-color: #d29922;
        }

        .diff-moved-out {
            background: rgba(88, 166, 255, 0.15);
            border-left-color: #58a6ff;
            color: #90caf9;
        }

        .diff-moved-in {
            background: rgba(88, 166, 255, 0.15);
            border-left-color: #58a6ff;
            color: #90caf9;
        }

        .diff-empty {
            background: transparent;
            color: transparent;
        }

        .word-added {
            background: rgba(63, 185, 80, 0.4);
            border-bottom: 2px solid #3fb950;
            padding: 0 2px;
        }

        .word-removed {
            background: rgba(248, 81, 73, 0.4);
            border-bottom: 2px solid #f85149;
            text-decoration: line-through;
            padding: 0 2px;
        }

        .char-added {
            background: #3fb950;
            color: #ffffff;
            padding: 1px 2px;
            border-radius: 2px;
        }

        .char-removed {
            background: #f85149;
            color: #ffffff;
            padding: 1px 2px;
            border-radius: 2px;
        }

        .loading {
            padding: 40px;
            text-align: center;
            color: #6e7681;
        }

        @media (max-width: 768px) {
            .diff-panels {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Improved Diff Demo (Standalone)</h1>

        <div class="controls">
            <div class="control-group">
                <label for="testCase">Select Test Case:</label>
                <select id="testCase">
                    <option value="technical">Technical Blog Post (section reordering, typos)</option>
                    <option value="creative">Creative Writing (word changes, merging)</option>
                    <option value="documentation">Documentation (structural changes)</option>
                </select>
            </div>

            <div class="control-group">
                <label>Options:</label>
                <div class="checkbox-group">
                    <label>
                        <input type="checkbox" id="detectMoves" checked>
                        Detect moved blocks
                    </label>
                    <label>
                        <input type="checkbox" id="ignoreWhitespace" checked>
                        Ignore whitespace
                    </label>
                </div>
            </div>

            <button onclick="runDiff()">Compare Versions</button>
        </div>

        <div id="diffContainer">
            <div class="stats-container">
                <div class="stat-item">
                    <span class="stat-dot added"></span>
                    <span id="addedCount">0 additions</span>
                </div>
                <div class="stat-item">
                    <span class="stat-dot removed"></span>
                    <span id="removedCount">0 deletions</span>
                </div>
                <div class="stat-item">
                    <span class="stat-dot modified"></span>
                    <span id="modifiedCount">0 modifications</span>
                </div>
                <div class="stat-item" id="movedStatsContainer" style="display: none;">
                    <span class="stat-dot moved"></span>
                    <span id="movedCount">0 blocks moved</span>
                </div>
            </div>

            <div class="diff-panels">
                <div class="diff-panel">
                    <div class="panel-header">Version 1 (Original)</div>
                    <div class="panel-content" id="diffLeft"></div>
                </div>
                <div class="diff-panel">
                    <div class="panel-header">Version 2 (Modified)</div>
                    <div class="panel-content" id="diffRight"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
// ============================================================================
// EMBEDDED: improved-diff.js
// ============================================================================
{diff_js_content}

// ============================================================================
// TEST DATA
// ============================================================================
const TEST_DATA = {test_data_json};

// ============================================================================
// DEMO FUNCTIONALITY
// ============================================================================
function runDiff() {
    const testCase = document.getElementById('testCase').value;
    const detectMoves = document.getElementById('detectMoves').checked;
    const ignoreWhitespace = document.getElementById('ignoreWhitespace').checked;

    const text1 = TEST_DATA[testCase].v1;
    const text2 = TEST_DATA[testCase].v2;

    console.log('Text1 length:', text1.length, 'Text2 length:', text2.length);

    document.getElementById('diffContainer').style.display = 'block';

    const loadingHTML = '<div class="loading">Computing diff...<br><small>Analyzing changes</small></div>';
    document.getElementById('diffLeft').innerHTML = loadingHTML;
    document.getElementById('diffRight').innerHTML = loadingHTML;

    setTimeout(() => {
        const differ = new ImprovedDiff({
            similarityThreshold: 0.3,
            moveDetectionThreshold: 0.85,
            ignoreWhitespace: ignoreWhitespace,
            detectMoves: detectMoves,
            minMoveBlockSize: 2
        });

        console.time('Diff computation');
        const diffResult = differ.computeDiff(text1, text2);
        console.timeEnd('Diff computation');

        console.log('Diff result:', diffResult);
        console.log('Stats:', diffResult.stats);
        console.log('Diff array length:', diffResult.diff ? diffResult.diff.length : 'undefined');
        if (diffResult.diff && diffResult.diff.length > 0) {
            console.log('First diff item:', diffResult.diff[0]);
            console.log('Last diff item:', diffResult.diff[diffResult.diff.length - 1]);
        }

        const rendered = differ.renderToHTML(diffResult);

        console.log('Left HTML length:', rendered.left.length, 'Right HTML length:', rendered.right.length);

        document.getElementById('diffLeft').innerHTML = rendered.left;
        document.getElementById('diffRight').innerHTML = rendered.right;

        const stats = diffResult.stats;
        document.getElementById('addedCount').textContent = `${stats.additions} addition${stats.additions !== 1 ? 's' : ''}`;
        document.getElementById('removedCount').textContent = `${stats.deletions} deletion${stats.deletions !== 1 ? 's' : ''}`;
        document.getElementById('modifiedCount').textContent = `${stats.modifications} modification${stats.modifications !== 1 ? 's' : ''}`;

        if (stats.moves > 0) {
            document.getElementById('movedStatsContainer').style.display = 'flex';
            document.getElementById('movedCount').textContent = `${Math.floor(stats.moves / 2)} block${stats.moves !== 2 ? 's' : ''} moved`;
        } else {
            document.getElementById('movedStatsContainer').style.display = 'none';
        }

        // Synchronized scrolling
        const leftPanel = document.querySelector('.diff-panel:nth-child(1) .panel-content');
        const rightPanel = document.querySelector('.diff-panel:nth-child(2) .panel-content');

        leftPanel.onscroll = () => {
            rightPanel.scrollTop = leftPanel.scrollTop;
        };

        rightPanel.onscroll = () => {
            leftPanel.scrollTop = rightPanel.scrollTop;
        };
    }, 100);
}

console.log('✅ Demo ready! Select a test case and click "Compare Versions"');
    </script>
</body>
</html>'''

# Generate the final HTML
test_data_json = json.dumps(test_samples, indent=2)

# Use string replacement instead of format to avoid CSS brace issues
final_html = html_template.replace('{diff_js_content}', diff_js)
final_html = final_html.replace('{test_data_json}', test_data_json)

# Write the standalone file
with open('diff_demo_standalone.html', 'w') as f:
    f.write(final_html)

print('✅ Generated diff_demo_standalone.html')
print(f'   - Embedded improved-diff.js ({len(diff_js)} characters)')
print(f'   - Embedded test data ({len(test_data_json)} characters)')
print(f'   - Total file size: {len(final_html)} characters')
