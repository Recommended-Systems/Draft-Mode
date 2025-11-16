#!/usr/bin/env python3
"""
Generate comparison demo showing V1 (Myers) vs V2 (Hierarchical) diff algorithms
"""

import os
import json

# Read both diff implementations
with open('../static/js/improved-diff.js', 'r') as f:
    diff_v1_js = f.read()

with open('../static/js/improved-diff-v2.js', 'r') as f:
    diff_v2_js = f.read()

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
    <title>Diff V1 vs V2 Comparison</title>
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
            max-width: 1800px;
            margin: 0 auto;
        }

        h1 {
            margin-bottom: 10px;
            color: #58a6ff;
        }

        .subtitle {
            color: #8b949e;
            margin-bottom: 20px;
            font-size: 14px;
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

        .algorithm-comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .algorithm-section {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: hidden;
        }

        .algorithm-header {
            background: #21262d;
            padding: 15px;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .algorithm-title {
            font-size: 16px;
            font-weight: 600;
        }

        .algorithm-badge {
            background: #238636;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .v1-badge {
            background: #58a6ff;
        }

        .v2-badge {
            background: #a371f7;
        }

        .stats-container {
            padding: 15px;
            border-bottom: 1px solid #30363d;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 13px;
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
            gap: 10px;
            padding: 10px;
        }

        .diff-panel {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow: auto;
            max-height: 500px;
            min-height: 200px;
        }

        .panel-header {
            background: #161b22;
            padding: 8px 12px;
            border-bottom: 1px solid #30363d;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            font-size: 12px;
        }

        .panel-content {
            padding: 10px;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.5;
        }

        /* V1 styling - line-based */
        .diff-line {
            display: flex;
            padding: 2px 0;
            border-left: 4px solid transparent;
        }

        .line-number {
            min-width: 40px;
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

        .diff-empty {
            background: transparent;
            color: transparent;
        }

        /* V2 styling - block-based */
        .diff-block {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid transparent;
        }

        .diff-block.diff-unchanged {
            background: transparent;
        }

        .diff-block.diff-added {
            background: rgba(63, 185, 80, 0.15);
            border-left-color: #3fb950;
        }

        .diff-block.diff-removed {
            background: rgba(248, 81, 73, 0.15);
            border-left-color: #f85149;
        }

        .diff-block.diff-modified {
            background: rgba(210, 153, 34, 0.15);
            border-left-color: #d29922;
        }

        .diff-block.diff-empty {
            background: transparent;
            min-height: 20px;
        }

        .block-content {
            white-space: pre-wrap;
            word-break: break-word;
        }

        /* Word-level changes - subtle styling */
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

        /* Character-level changes - more prominent styling */
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

        /* Punctuation-level changes - very subtle styling */
        .punct-added {
            background: rgba(63, 185, 80, 0.2);
            border-bottom: 1px dotted #3fb950;
            padding: 0 1px;
        }

        .punct-removed {
            background: rgba(248, 81, 73, 0.2);
            border-bottom: 1px dotted #f85149;
            padding: 0 1px;
        }

        /* Merged blocks indicator */
        .merged-indicator {
            background: rgba(88, 166, 255, 0.15);
            border-left: 3px solid #58a6ff;
            padding: 4px 8px;
            margin-bottom: 8px;
            font-size: 11px;
            color: #58a6ff;
            font-weight: 600;
        }

        .merged-content-separator {
            border-top: 1px dashed #30363d;
            padding-top: 8px;
            margin-top: 8px;
            font-size: 11px;
            color: #6e7681;
            font-style: italic;
        }

        .loading {
            padding: 40px;
            text-align: center;
            color: #6e7681;
        }

        @media (max-width: 1400px) {
            .algorithm-comparison {
                grid-template-columns: 1fr;
            }
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
        <h1>Diff Algorithm Comparison: V1 vs V2</h1>
        <p class="subtitle">
            <strong>V1 (Myers):</strong> Line-based algorithm designed for source code<br>
            <strong>V2 (Hierarchical):</strong> Block-based algorithm designed for document/draft comparison
        </p>

        <div class="controls">
            <div class="control-group">
                <label for="testCase">Select Test Case:</label>
                <select id="testCase">
                    <option value="creative">Creative Writing (paragraph merging, word changes)</option>
                    <option value="technical">Technical Blog Post (section reordering, typos)</option>
                    <option value="documentation">Documentation (structural changes)</option>
                </select>
            </div>

            <button onclick="runComparison()">Compare Algorithms</button>
        </div>

        <div class="algorithm-comparison" id="comparisonContainer" style="display: none;">
            <!-- V1 Section -->
            <div class="algorithm-section">
                <div class="algorithm-header">
                    <span class="algorithm-title">V1: Myers Algorithm</span>
                    <span class="algorithm-badge v1-badge">LINE-BASED</span>
                </div>
                <div class="stats-container" id="v1Stats">
                    <div class="stat-item">
                        <span class="stat-dot added"></span>
                        <span id="v1AddedCount">0 additions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-dot removed"></span>
                        <span id="v1RemovedCount">0 deletions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-dot modified"></span>
                        <span id="v1ModifiedCount">0 modifications</span>
                    </div>
                </div>
                <div class="diff-panels">
                    <div class="diff-panel">
                        <div class="panel-header">Version 1 (Original)</div>
                        <div class="panel-content" id="v1DiffLeft"></div>
                    </div>
                    <div class="diff-panel">
                        <div class="panel-header">Version 2 (Modified)</div>
                        <div class="panel-content" id="v1DiffRight"></div>
                    </div>
                </div>
            </div>

            <!-- V2 Section -->
            <div class="algorithm-section">
                <div class="algorithm-header">
                    <span class="algorithm-title">V2: Hierarchical Algorithm</span>
                    <span class="algorithm-badge v2-badge">BLOCK-BASED</span>
                </div>
                <div class="stats-container" id="v2Stats">
                    <div class="stat-item">
                        <span class="stat-dot added"></span>
                        <span id="v2BlocksAdded">0 blocks added</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-dot removed"></span>
                        <span id="v2BlocksRemoved">0 blocks removed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-dot modified"></span>
                        <span id="v2BlocksModified">0 blocks modified</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-dot modified"></span>
                        <span id="v2WordsChanged">0 words changed</span>
                    </div>
                </div>
                <div class="diff-panels">
                    <div class="diff-panel">
                        <div class="panel-header">Version 1 (Original)</div>
                        <div class="panel-content" id="v2DiffLeft"></div>
                    </div>
                    <div class="diff-panel">
                        <div class="panel-header">Version 2 (Modified)</div>
                        <div class="panel-content" id="v2DiffRight"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
// ============================================================================
// V1: Myers Algorithm
// ============================================================================
{diff_v1_js}

// ============================================================================
// V2: Hierarchical Algorithm
// ============================================================================
{diff_v2_js}

// ============================================================================
// TEST DATA
// ============================================================================
const TEST_DATA = {test_data_json};

// ============================================================================
// COMPARISON FUNCTIONALITY
// ============================================================================
function runComparison() {
    const testCase = document.getElementById('testCase').value;
    const text1 = TEST_DATA[testCase].v1;
    const text2 = TEST_DATA[testCase].v2;

    document.getElementById('comparisonContainer').style.display = 'grid';

    // Show loading state
    const loadingHTML = '<div class="loading">Computing diff...</div>';
    document.getElementById('v1DiffLeft').innerHTML = loadingHTML;
    document.getElementById('v1DiffRight').innerHTML = loadingHTML;
    document.getElementById('v2DiffLeft').innerHTML = loadingHTML;
    document.getElementById('v2DiffRight').innerHTML = loadingHTML;

    setTimeout(() => {
        // Run V1 (Myers)
        console.log('=== V1 (Myers) ===');
        const v1Differ = new ImprovedDiff({
            similarityThreshold: 0.3,
            moveDetectionThreshold: 0.85,
            ignoreWhitespace: true,
            detectMoves: true,
            minMoveBlockSize: 2
        });

        console.time('V1 computation');
        const v1Result = v1Differ.computeDiff(text1, text2);
        console.timeEnd('V1 computation');
        console.log('V1 stats:', v1Result.stats);

        const v1Rendered = v1Differ.renderToHTML(v1Result);
        document.getElementById('v1DiffLeft').innerHTML = v1Rendered.left;
        document.getElementById('v1DiffRight').innerHTML = v1Rendered.right;

        // Update V1 stats
        const v1Stats = v1Result.stats;
        document.getElementById('v1AddedCount').textContent = `${v1Stats.additions} addition${v1Stats.additions !== 1 ? 's' : ''}`;
        document.getElementById('v1RemovedCount').textContent = `${v1Stats.deletions} deletion${v1Stats.deletions !== 1 ? 's' : ''}`;
        document.getElementById('v1ModifiedCount').textContent = `${v1Stats.modifications} modification${v1Stats.modifications !== 1 ? 's' : ''}`;

        // Run V2 (Hierarchical)
        console.log('\\n=== V2 (Hierarchical) ===');
        const v2Differ = new ImprovedDiffV2({
            structuralMatchThreshold: 0.5,
            wordMatchThreshold: 0.6,
            detectMoves: true,
            minMoveBlockSize: 5
        });

        console.time('V2 computation');
        const v2Result = v2Differ.computeDiff(text1, text2);
        console.timeEnd('V2 computation');
        console.log('V2 stats:', v2Result.stats);
        console.log('V2 blocks parsed:', {
            v1: v2Result.blocks1.length,
            v2: v2Result.blocks2.length
        });

        const v2Rendered = v2Differ.renderToHTML(v2Result);
        document.getElementById('v2DiffLeft').innerHTML = v2Rendered.left;
        document.getElementById('v2DiffRight').innerHTML = v2Rendered.right;

        // Update V2 stats
        const v2Stats = v2Result.stats;
        document.getElementById('v2BlocksAdded').textContent = `${v2Stats.blocksAdded} block${v2Stats.blocksAdded !== 1 ? 's' : ''} added`;
        document.getElementById('v2BlocksRemoved').textContent = `${v2Stats.blocksRemoved} block${v2Stats.blocksRemoved !== 1 ? 's' : ''} removed`;
        document.getElementById('v2BlocksModified').textContent = `${v2Stats.blocksModified} block${v2Stats.blocksModified !== 1 ? 's' : ''} modified`;

        const totalWordChanges = v2Stats.wordsAdded + v2Stats.wordsRemoved + v2Stats.wordsModified;
        document.getElementById('v2WordsChanged').textContent = `${totalWordChanges} word${totalWordChanges !== 1 ? 's' : ''} changed`;
    }, 100);
}

console.log('✅ Comparison demo ready! Select a test case and click "Compare Algorithms"');
    </script>
</body>
</html>'''

# Generate the final HTML
test_data_json = json.dumps(test_samples, indent=2)

# Use string replacement to avoid format string issues
final_html = html_template.replace('{diff_v1_js}', diff_v1_js)
final_html = final_html.replace('{diff_v2_js}', diff_v2_js)
final_html = final_html.replace('{test_data_json}', test_data_json)

# Write the comparison file
with open('diff_comparison_v1_vs_v2.html', 'w') as f:
    f.write(final_html)

print('✅ Generated diff_comparison_v1_vs_v2.html')
print(f'   - Embedded V1 (Myers): {len(diff_v1_js)} characters')
print(f'   - Embedded V2 (Hierarchical): {len(diff_v2_js)} characters')
print(f'   - Test data: {len(test_data_json)} characters')
print(f'   - Total file size: {len(final_html)} characters')
