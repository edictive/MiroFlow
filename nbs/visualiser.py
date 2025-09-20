import re
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
from pathlib import Path

def extract_question_text(task_data):
    """Extract the core question from task description"""
    desc = task_data['input']['task_description']
    # Extract the prediction question
    match = re.search(r'"([^"]*vs[^"]*around[^"]*)\.', desc)
    if match:
        return match.group(1)
    # Fallback to first line
    return desc.split('.')[0][:100] + "..."

def extract_main_agent_reasoning(message_history):
    """Extract main agent reasoning steps and tool calls"""
    events = []
    messages = message_history['message_history']
    
    for i, msg in enumerate(messages):
        if msg['role'] == 'assistant':
            content = msg['content']
            
            # Check for tool calls
            if '<use_mcp_tool>' in content:
                # Extract tool call details
                tool_match = re.search(r'<tool_name>([^<]+)</tool_name>', content)
                args_match = re.search(r'"subtask":\s*"([^"]+)"', content)
                
                tool_name = tool_match.group(1) if tool_match else "unknown_tool"
                subtask = args_match.group(1)[:80] + "..." if args_match and len(args_match.group(1)) > 80 else args_match.group(1) if args_match else "unknown subtask"
                
                events.append({
                    'type': 'TOOL_CALL',
                    'tool': tool_name,
                    'purpose': subtask,
                    'index': i
                })
            else:
                # Final reasoning/answer
                if '\\boxed{' in content:
                    events.append({
                        'type': 'FINAL_DECISION',
                        'reasoning': content[:100].strip() + "...",
                        'index': i
                    })
    
    return events

def extract_sub_agent_results(message_history, sub_sessions):
    """Extract sub-agent session results"""
    results = []
    messages = message_history['message_history']
    
    # Find tool results (user messages after tool calls)
    for i, msg in enumerate(messages):
        if msg['role'] == 'user' and i > 1:  # Skip initial user message
            content = msg['content'][0]['text'] if msg['content'] else ""
            
            # Check if this is a tool result with failure
            if 'could not be completed' in content or 'FINAL ANSWER' in content:
                # Extract the key failure reason
                if 'file path' in content and 'did not exist' in content:
                    failure_reason = "File not found"
                elif 'tool limitations' in content or 'internet-based searches' in content:
                    failure_reason = "No internet access"
                else:
                    failure_reason = "Task failed"
                
                results.append({
                    'type': 'SUB_AGENT_RESULT',
                    'outcome': 'FAILED',
                    'reason': failure_reason,
                    'index': i
                })
    
    return results

def build_execution_flow(task_data):
    """Build the complete execution flow"""
    flow = []
    
    # 1. Question
    question = extract_question_text(task_data)
    flow.append({
        'id': 'question',
        'type': 'QUESTION',
        'label': 'QUESTION',
        'content': question,
        'node_color': '#E8F4FD'
    })
    
    # 2. Extract reasoning and tool calls
    main_events = extract_main_agent_reasoning(task_data['main_agent_message_history'])
    sub_results = extract_sub_agent_results(
        task_data['main_agent_message_history'], 
        task_data['sub_agent_message_history_sessions']
    )
    
    # 3. Merge and sort events
    all_events = main_events + sub_results
    all_events.sort(key=lambda x: x['index'])
    
    # 4. Convert to flow nodes
    node_id = 1
    for event in all_events:
        if event['type'] == 'TOOL_CALL':
            flow.append({
                'id': f'tool_{node_id}',
                'type': 'TOOL_CALL',
                'label': f'TOOL CALL: {event["tool"]}',
                'content': event['purpose'],
                'node_color': '#FFF2CC'
            })
        elif event['type'] == 'SUB_AGENT_RESULT':
            color = '#FFE6E6' if event['outcome'] == 'FAILED' else '#E6F7E6'
            flow.append({
                'id': f'result_{node_id}',
                'type': 'SUB_AGENT_RESULT',
                'label': f'SUB-AGENT: {event["outcome"]}',
                'content': event['reason'],
                'node_color': color
            })
        node_id += 1
    
    # 5. Final answer
    flow.append({
        'id': 'answer',
        'type': 'ANSWER',
        'label': 'FINAL ANSWER',
        'content': task_data['final_boxed_answer'],
        'node_color': '#E6F7E6'
    })
    
    return flow

def build_execution_flow_dag(task_data):
    """Build a DAG-style execution flow capturing parallel sub-agents.

    Returns a dict with keys:
      - nodes: list of dicts with id, type, label, content, node_color, lane, x, y, height
      - edges: list of (source_id, target_id)
    """
    # Visual parameters to keep consistent with renderer
    node_spacing = 0.4
    label_chars_per_line = 32
    content_chars_per_line = 48

    nodes = []
    edges = []
    edge_types = {}

    # Main lane nodes
    question = extract_question_text(task_data)
    main_nodes = []
    main_nodes.append({
        'id': 'main_question',
        'type': 'QUESTION',
        'label': 'QUESTION',
        'content': question,
        'node_color': '#E8F4FD',
        'lane': 'main'
    })

    main_events = extract_main_agent_reasoning(task_data['main_agent_message_history'])
    tool_call_ids = []
    for ev in main_events:
        if ev['type'] == 'TOOL_CALL':
            node_id = f"main_tool_{len(tool_call_ids)+1}"
            main_nodes.append({
                'id': node_id,
                'type': 'TOOL_CALL',
                'label': f"TOOL CALL: {ev['tool']}",
                'content': ev['purpose'],
                'node_color': '#FFF2CC',
                'lane': 'main'
            })
            tool_call_ids.append(node_id)

    main_nodes.append({
        'id': 'main_answer',
        'type': 'ANSWER',
        'label': 'FINAL ANSWER',
        'content': task_data['final_boxed_answer'],
        'node_color': '#E6F7E6',
        'lane': 'main'
    })

    # Position main lane vertically at x=0
    y_offset = 0.0
    for n in main_nodes:
        h = calculate_node_height(n['label'], n['content'], max_width=label_chars_per_line, content_width=content_chars_per_line)
        n['height'] = h
        n['x'] = 0.0
        n['y'] = -y_offset - h / 2.0
        y_offset += h + node_spacing

    # Edges along the main lane
    for i in range(len(main_nodes) - 1):
        e = (main_nodes[i]['id'], main_nodes[i+1]['id'])
        edges.append(e)
        edge_types[e] = 'main'

    # Sub-agent lanes
    sub_sessions = task_data.get('sub_agent_message_history_sessions', {})
    session_keys = sorted(sub_sessions.keys())

    def _parse_subtask_from_text(text: str) -> str:
        m = re.search(r"'subtask':\s*'([^']+)'", text)
        return (m.group(1) if m else text)[:140] + ("..." if len(text) > 140 else "")

    def _extract_sub_agent_nodes(session_obj):
        mh = session_obj.get('message_history', [])
        sub_nodes = []
        # Start node with subtask preview if available
        subtask_preview = ''
        for msg in mh:
            if msg.get('role') == 'user':
                c = msg.get('content', [])
                if isinstance(c, list) and c:
                    subtask_preview = _parse_subtask_from_text(c[0].get('text', ''))
                    break
        sub_nodes.append({
            'type': 'SUB_AGENT',
            'label': 'SUB-AGENT START',
            'content': subtask_preview or 'Subtask started',
            'node_color': '#E8F4FD'
        })

        for msg in mh:
            role = msg.get('role')
            if role == 'assistant':
                content = msg.get('content', '')
                if isinstance(content, str) and '<use_mcp_tool>' in content:
                    tool_match = re.search(r'<tool_name>([^<]+)</tool_name>', content)
                    tool_name = tool_match.group(1) if tool_match else 'tool'
                    arg_match = re.search(r'"uri"\s*:\s*"([^"]+)"', content) or re.search(r'"subtask"\s*:\s*"([^"]+)"', content)
                    arg_preview = arg_match.group(1) if arg_match else ''
                    sub_nodes.append({
                        'type': 'TOOL_CALL',
                        'label': f'TOOL: {tool_name}',
                        'content': (arg_preview[:100] + '...') if len(arg_preview) > 100 else arg_preview,
                        'node_color': '#FFF2CC'
                    })
                elif isinstance(content, str) and ('FINAL ANSWER' in content or 'The task' in content):
                    sub_nodes.append({
                        'type': 'SUB_AGENT_RESULT',
                        'label': 'SUB-AGENT SUMMARY',
                        'content': content[:140] + ('...' if len(content) > 140 else ''),
                        'node_color': '#E6F7E6'
                    })
            elif role == 'user':
                c = msg.get('content', [])
                if isinstance(c, list) and c:
                    text = c[0].get('text', '')
                    first_line = text.split('\n', 1)[0]
                    if 'Error' in first_line or 'could not be completed' in text or 'Note:' in text:
                        sub_nodes.append({
                            'type': 'SUB_AGENT_RESULT',
                            'label': 'RESULT',
                            'content': first_line[:140],
                            'node_color': '#FFE6E6'
                        })
        return sub_nodes

    for idx, key in enumerate(session_keys):
        if idx >= len(tool_call_ids):
            break
        session_obj = sub_sessions[key]
        parent_tool_id = tool_call_ids[idx]
        parent_index = next(i for i, n in enumerate(main_nodes) if n['id'] == parent_tool_id)
        next_main_id = main_nodes[parent_index + 1]['id'] if parent_index + 1 < len(main_nodes) else 'main_answer'

        # Alternate lanes left/right
        lane_name = f'sub_{idx+1}'
        lane_x = -12.0 if (idx % 2 == 0) else 12.0

        raw_nodes = _extract_sub_agent_nodes(session_obj)
        # Position sub-lane starting slightly below the parent
        sub_y_offset = 0.2
        parent_y = next(n['y'] for n in main_nodes if n['id'] == parent_tool_id)
        positioned = []
        for j, sn in enumerate(raw_nodes):
            node_id = f'{lane_name}_{j+1}'
            h = calculate_node_height(sn['label'], sn['content'], max_width=label_chars_per_line, content_width=content_chars_per_line)
            y_center = parent_y - sub_y_offset - h / 2.0
            positioned.append({
                'id': node_id,
                'type': sn['type'],
                'label': sn['label'],
                'content': sn['content'],
                'node_color': sn['node_color'],
                'lane': lane_name,
                'x': lane_x,
                'y': y_center,
                'height': h
            })
            sub_y_offset += h + node_spacing

        if positioned:
            # Align first sub node horizontally with parent tool call center (clean branch arrow)
            positioned[0]['y'] = parent_y
            # Connect from main tool call to first sub-node (double arrow branch)
            e = (parent_tool_id, positioned[0]['id'])
            edges.append(e)
            edge_types[e] = 'branch'
            # Sub-lane internal edges (vertical down)
            for a, b in zip(positioned, positioned[1:]):
                e = (a['id'], b['id'])
                edges.append(e)
                edge_types[e] = 'sub'
            # Connect back to next main node (horizontal join)
            e = (positioned[-1]['id'], next_main_id)
            edges.append(e)
            edge_types[e] = 'join'

        nodes.extend(positioned)

    # Add main nodes last for potential overdraw
    nodes.extend(main_nodes)

    return {'nodes': nodes, 'edges': edges, 'edge_types': edge_types}

def create_flow_graph(flow_events):
    """Create NetworkX graph from flow events"""
    G = nx.DiGraph()
    
    # Add nodes
    for event in flow_events:
        G.add_node(
            event['id'],
            label=event['label'],
            content=event['content'],
            node_type=event['type'],
            color=event['node_color']
        )
    
    # Add edges (linear flow)
    for i in range(len(flow_events) - 1):
        G.add_edge(flow_events[i]['id'], flow_events[i+1]['id'])
    
    return G

def create_graph_from_dag(dag):
    """Create a NetworkX graph from a dag dict returned by build_execution_flow_dag.
    Stores precomputed positions in node attribute 'pos'.
    """
    G = nx.DiGraph()
    for n in dag['nodes']:
        G.add_node(
            n['id'],
            label=n['label'],
            content=n['content'],
            node_type=n['type'],
            color=n['node_color'],
            pos=(n['x'], n['y'])
        )
    for src, dst in dag['edges']:
        et = dag.get('edge_types', {}).get((src, dst), 'main')
        G.add_edge(src, dst, etype=et)
    return G

def wrap_text(text, max_chars_per_line=32):
    """Wrap text to fit within node width.

    - Uses a greedy word-wrap by spaces
    - Additionally breaks overlong tokens (e.g., long URIs, IDs) so they don't spill
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    def flush_line():
        nonlocal current_line, current_length
        if current_line:
            lines.append(' '.join(current_line))
            current_line = []
            current_length = 0

    for word in words:
        # If a single token exceeds the max width, hard-break it into chunks
        if len(word) > max_chars_per_line:
            flush_line()
            start = 0
            while start < len(word):
                chunk = word[start:start + max_chars_per_line]
                lines.append(chunk)
                start += max_chars_per_line
            continue

        # Normal greedy packing
        additional = len(word) + (1 if current_length > 0 else 0)
        if current_length + additional <= max_chars_per_line:
            current_line.append(word)
            current_length += additional
        else:
            flush_line()
            current_line.append(word)
            current_length = len(word)

    flush_line()
    return '\n'.join(lines)

def calculate_node_height(label, content, max_width=32, content_width=None):
    """Calculate required height for node based on text content.

    If content_width is provided, it will be used for wrapping the content text,
    allowing content to take more horizontal space than the label.
    """
    label_lines = len(wrap_text(label, max_width).split('\n'))
    effective_content_width = content_width if content_width is not None else max_width
    content_lines = len(wrap_text(content, effective_content_width).split('\n'))

    # More compact sizing
    base_height = 1
    line_height = 0.16
    padding = 0.2

    return base_height + (label_lines + content_lines) * line_height + padding

def visualize_execution_graph_scaled(G, scale=0.5, task_data=None):
    """Render a uniformly scaled (fonts, strokes, figure size) execution flow.
    Keeps node geometry (data-units) the same, shrinks the rendered size.
    """
    nodes = list(G.nodes())

    # Layout parameters (data units)
    node_spacing = 0.4
    box_width = 8.0
    label_chars_per_line = 32
    content_chars_per_line = 58  # ~20% wider content utilization

    # Pre-compute node heights (data units)
    node_heights = {}
    for node in nodes:
        node_data = G.nodes[node]
        node_heights[node] = calculate_node_height(
            node_data['label'],
            node_data['content'],
            max_width=label_chars_per_line,
            content_width=content_chars_per_line,
        )

    # Positions: use provided node 'pos' if available, else linear layout
    pos = {}
    if all('pos' in G.nodes[n] for n in nodes):
        for n in nodes:
            pos[n] = G.nodes[n]['pos']
    else:
        y_offset = 0.0
        for n in nodes:
            h = node_heights[n]
            pos[n] = (0.0, -y_offset - h / 2.0)
            y_offset += h + node_spacing

    # Bounds
    min_y = min(pos[n][1] - node_heights[n] / 2.0 for n in nodes)
    max_y = max(pos[n][1] + node_heights[n] / 2.0 for n in nodes)

    # Base figure size then scale
    content_height = (max_y - min_y) + 0.8
    fig_height_base = min(max(content_height * 0.9, 6), 12)
   
    # Compute horizontal extent
    min_x = min(pos[n][0] - box_width / 2.0 for n in nodes)
    max_x = max(pos[n][0] + box_width / 2.0 for n in nodes)
    fig_width = max(10, (max_x - min_x) + 1.2) * scale
    fig_height = fig_height_base * scale

    # Scaled style
    lw = 2.0 * scale
    rect_lw = 2.0 * scale
    shrink = 3.0 * scale
    box_pad = 0.12 * scale
    label_fs = max(6, int(round(12 * scale)))
    content_fs = max(6, int(round(10 * scale)))
    title_fs = max(8, int(round(16 * scale)))
    title_pad = 10 * scale

    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))

    # Helpers for clean orthogonal connectors
    def _bottom(p, h):
        return (p[0], p[1] - h / 2.0)
    def _top(p, h):
        return (p[0], p[1] + h / 2.0)
    def _left(p):
        return (p[0] - box_width / 2.0, p[1])
    def _right(p):
        return (p[0] + box_width / 2.0, p[1])

    def draw_h_arrow(p1, p2, style='->'):
        ax.annotate(
            "",
            xy=p2,
            xytext=p1,
            arrowprops=dict(arrowstyle=style, color='#555555', lw=lw, shrinkA=shrink, shrinkB=shrink),
        )

    def draw_v_arrow(p1, p2):
        ax.annotate(
            "",
            xy=p2,
            xytext=p1,
            arrowprops=dict(arrowstyle='->', color='#555555', lw=lw, shrinkA=shrink, shrinkB=shrink),
        )

    # Edges
    for start_node, end_node, data in G.edges(data=True):
        etype = data.get('etype', 'main')
        sp = pos[start_node]
        ep = pos[end_node]
        sh = node_heights[start_node]
        eh = node_heights[end_node]

        if etype == 'main' or etype == 'sub':
            # Vertical connection downwards
            start_pt = _bottom(sp, sh)
            end_pt = _top(ep, eh)
            draw_v_arrow(start_pt, end_pt)
        elif etype == 'branch':
            # Horizontal double arrow from main tool call to sub-agent first node
            if ep[0] < sp[0]:
                start_pt = _left(sp)
                end_pt = _right(ep)
            else:
                start_pt = _right(sp)
                end_pt = _left(ep)
            draw_h_arrow(start_pt, end_pt, style='<->')
        elif etype == 'join':
            # Horizontal join back to next main node
            if ep[0] < sp[0]:
                start_pt = _left(sp)
                end_pt = _right(ep)
            else:
                start_pt = _right(sp)
                end_pt = _left(ep)
            draw_h_arrow(start_pt, end_pt, style='->')

    # Nodes
    for node in nodes:
        x, y = pos[node]
        node_data = G.nodes[node]
        h = node_heights[node]

        rect = patches.FancyBboxPatch(
            (x - box_width / 2.0, y - h / 2.0),
            box_width,
            h,
            boxstyle=f"round,pad={box_pad}",
            facecolor=node_data['color'],
            edgecolor='#333333',
            linewidth=rect_lw,
        )
        ax.add_patch(rect)

        wrapped_label = wrap_text(node_data['label'], label_chars_per_line)
        ax.text(x, y + h / 4.0, wrapped_label, ha='center', va='center', fontsize=label_fs, fontweight='bold', color='#000000')

        wrapped_content = wrap_text(node_data['content'], content_chars_per_line)
        ax.text(x, y - h / 4.0, wrapped_content, ha='center', va='center', fontsize=content_fs, style='italic', color='#444444')

    # Axes
    margin_x = 0.4
    ax.set_xlim(min_x - margin_x, max_x + margin_x)
    ax.set_ylim(min_y - 0.3, max_y + 0.4)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    plt.title(f"Task Execution Flow: {task_data['task_id'][:16]}...", fontsize=title_fs, fontweight='bold', pad=title_pad)

    plt.subplots_adjust(top=0.92, bottom=0.05)
    plt.tight_layout()
    plt.show()