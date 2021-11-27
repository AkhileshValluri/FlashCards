from jinja2 import *
import matplotlib.pyplot as plt
import sys

inp1 = sys.argv[1]  # input('Enter c or s :  ')
inp2 = sys.argv[2]  # input('Enter id : ')
a = open('data.csv')
r = a.readlines()
dt = []
ii = 0
for x in (r[1:]):
    d = {'student_id': None, 'course_id': None, 'marks': None}
    l = x.strip().split(',')
    d['student_id'] = l[0]
    d['course_id'] = l[1].strip()
    d['marks'] = l[2]
    dt.append(d)
a.close()
mm = 0
if inp1 == '-s':
    for x in dt:
        if x['student_id'] == inp2:
            mm += int(x['marks'])
            ii += 1
mx = 0
avge = 0
i = 0
marks_data = {}
if inp1 == '-c' :
    for x in dt:
        if x['course_id'] == inp2:
            avge += int(x['marks'])
            i += 1
            if int(x['marks']) > mx:
                mx = int(x['marks'])
            try:
                marks_data[x['marks']] += 1
            except:
                marks_data[x['marks']] = 1
            if inp1 == '-c':
                avg_marks = avge / i

fi = '''<! DOCTYPE html>
<html>
<title>Student Data</title>
<body>
<h1>Student Details</h1>
<div id='main'>
<table border=1px>
    <thead>
        <tr>
            <th>Student id</th>
            <th>Course id</th>
            <th>Marks</th>
        </tr>
    </thead>
<tbody>
{% for group in dt | groupby("student_id") %}{% for x in group.list %}{% if x.student_id == inp2 %}
<tr>
    <td>{{x.student_id}}</td>
    <td>{{x.course_id}}</td> 
    <td>{{x.marks}}</td>
</tr>
{% endif %}{% endfor %}{% endfor %}
</tbody>
<tr><td colspan='2' align='center'>Total marks</td><td>{{mm}}</td>
</table>
</div>
</body>
</html>'''

fii = '''<! DOCTYPE html>
<html>
<title>Course Data</title>
<body>
<h1>Course Details</h1>
<div id='main'>
    <table border=1px>
        <thead>
            <tr>
                <th>Average Marks</th>
                <th>Maximum Marks</th> 
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{{avg_marks}}</td>
                <td>{{mx}}</td>
            </tr>
        </tbody>
    </table>
</div>
<img src='samplefigure.png'></body>
</html>'''

fiii = '''<! DOCTYPE html>
<html>
<title>Something went wrong</title>
<body>
<h1>Wrong Inputs</h1>
<p>Something went wrong</p>
</body>
</html>'''



if  inp1 == '-s':
    content = Template(fi).render(dt=dt, mm=mm, inp2=inp2)
    fls = open('output.html', 'w')
    fls.write(content)
    fls.close()
    

if inp1 == '-c':
    if ii !=0 or i!=0:
        marks = list(marks_data.keys())
        frequency = list(marks_data.values())
        test = plt.figure()
        plt.bar(marks, frequency)
        plt.xlabel('marks')
        plt.ylabel('frequency')
        plt.figure(figsize=(50, 50))
        test.savefig('samplefigure.png')
        test.show()

        content = Template(fii).render(avg_marks=avg_marks, mx=mx, a=a, inp2=int(inp2))
        fls = open('output.html', 'w')
        fls.write(content)
        fls.close()
    
if (inp1 != '-c' and inp1 != '-s') or (ii == 0 and i == 0):
    #print("test --s--",inp1, inp2)
    content = Template(fiii).render()
    fls = open('output.html', 'w')
    fls.write(content)
    fls.close()    
