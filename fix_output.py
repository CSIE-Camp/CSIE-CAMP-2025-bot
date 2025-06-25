output = ''
with open('output','r',encoding='utf-16') as f:
    line=f.readline()
    i = 1
    while line!='':
        # print(line)
        line = line.strip()
        output += f'<sentence{i}>' + line + f'</sentence{i}>\n'
        i += 1
        line=f.readline()

with open('output','w',encoding='utf-16') as f:
    f.write(output)