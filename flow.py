import graphviz

def create_flowchart(code):
    graph = graphviz.Digraph()
    graph.attr('node', shape='box')

    blocks = code.split('\n')

    block_stack = ['start']
    graph.node(block_stack[-1], 'Start', shape='ellipse')

    for i, line in enumerate(blocks, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        next_block = f'block{i}'
        if 'if' in line or 'elif' in line:
            graph.node(next_block, line, shape='diamond')
            graph.edge(block_stack[-1], next_block)
            block_stack.append(next_block)
        elif 'else' in line:
            else_block = f'else{i}'
            graph.node(else_block, line, shape='diamond')
            if_block = block_stack[-1]
            graph.edge(if_block, else_block, label='false')
            block_stack[-1] = else_block  # Replace the top with else
        elif 'for' in line or 'while' in line:
            graph.node(next_block, line, shape='parallelogram')
            graph.edge(block_stack[-1], next_block)
            block_stack.append(next_block)
        elif 'break' in line or 'continue' in line:
            graph.node(next_block, line, shape='hexagon')
            graph.edge(block_stack[-1], next_block)
            if 'break' in line:
                # Link back to the loop start if it's a 'continue'
                graph.edge(next_block, 'end', label='break')
            else:
                # Link to the end of the loop for 'break'
                loop_start = block_stack[-2]  # The second last item is the loop start
                graph.edge(next_block, loop_start, label='continue')
        else:
            graph.node(next_block, line, shape='rectangle')
            graph.edge(block_stack[-1], next_block)
            if len(block_stack) > 1 and ('if' in blocks[i-2] or 'else' in blocks[i-2]):
                # Link back to the end of the condition
                condition_end = f'end{block_stack[-2]}'
                graph.node(condition_end, '', shape='point')
                graph.edge(next_block, condition_end)
                graph.edge(block_stack[-2], condition_end, label='false')
                block_stack.pop()  # Pop condition block

        if 'if' not in line and 'else' not in line:
            block_stack[-1] = next_block  # Update the current block

    graph.node('end', 'End', shape='ellipse')
    if block_stack:
        graph.edge(block_stack[-1], 'end')
    return graph




with open('./test.py', 'r') as file:
    code = file.read()

flowchart = create_flowchart(code)
flowchart.render('output', format='png', cleanup=True)
