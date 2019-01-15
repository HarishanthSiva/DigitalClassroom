import argparse
import cv2
import math
import numpy as np
import tkMessageBox as box
import paramiko
import os,sys,cv2,random,datetime
import Tkinter as ttk
import json
from ttk import *
from Tkinter import*
from PIL import ImageTk,Image
from scp import SCPClient, SCPException, put, get,asbytes

refPt = []
cropping = False
points=[]
z=-1

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    #key = paramiko.RSAKey(data=base64.b64decode(b"""AAAAB3Nza..."""), password='my key password')
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def find_key(input_dict, value):
    return {k for k, v in input_dict.items() if v == value}

def distance((a,b),(c,d)):
    return (math.sqrt((a-c)**2+(b-d)**2))

def angle((a,b),(c,d)):
    if a==c:
        if b==d:
            return(0)
        elif b<d:
            return (90)
        else:
            return(-90)
    elif b==d:
        if a<c:
            return(0)
        else:
            return(180)
    else:
        tem=math.degrees(math.atan((d-b)/(c-a)))
        if (a>c) & (b<d):
            return(180+tem)
        elif(a<c) & (b<d):
            return(tem)
        elif (a<c) & (b>d):
            return(tem)
        else:
            return(-180+tem)

#print(angle(cordinate_dictionary["hari"],cordinate_dictionary["piri"]))
#print(distance(cordinate_dictionary["athavan"],cordinate_dictionary["nilaki"]))
def create_distance(a,unallocated):
    min_dist = float("inf")
    min_id = None
    global cordinate_dictionary
    for key in unallocated:
        if key != a:
            dist = distance(cordinate_dictionary[key],cordinate_dictionary[a])
            if dist < min_dist:
                min_dist = dist
                min_id = key
    return min_id, min_dist

def find_short_neighbour(allocated,unallocated):
    min_dist = float("inf")
    min_id = None
    min_source = None
    for person in allocated:
        id, dist = create_distance(person, unallocated)
        if (dist < min_dist):
            min_dist = dist
            min_id = id
            min_source = person

    return min_source, min_id

def place(degree,(i,j)):
    place_holder=round(degree/45)
    if (place_holder==0):
            new_cordinate=(i+1,j)
    elif(place_holder==1):
            new_cordinate=(i+1,j+1)
    elif (place_holder == 2):
        new_cordinate = (i, j + 1)
    elif (place_holder == 3):
        new_cordinate = (i-1, j + 1)
    elif (place_holder == 4):
        new_cordinate = (i-1, j )
    elif (place_holder == -1):
        new_cordinate = (i + 1, j - 1)
    elif (place_holder == -2):
        new_cordinate = (i, j-1)
    elif (place_holder == -3):
        new_cordinate = (i - 1, j - 1)
    elif (place_holder == -4):
        new_cordinate = (i - 1, j)

    return new_cordinate
def check(p1,p3,point_dict):
	x1=p1[0]
	y1=p1[1]
	x3=p3[0]
	y3=p3[1]
	x2=x1
	y2=y3
	x4=x3
	y4=y1
	d=[[x1,y1],[x2,y2],[x3,y3],[x4,y4],[x1,y1]]
	return_list=[]
	for person in point_dict:
		point=point_dict[person]
		xp = point[0]
		yp = point[1]
		for i in range (0,4):
			#D = (x2 - x1) * (yp - y1) - (xp - x1) * (y2 - y1)
			D=(d[i+1][0]-d[i][0])*(yp-d[i][1])-(xp-d[i][0])*(d[i+1][1]-d[i][1])
			if D>0:
				break
		else:
			return_list.append(person)
	return return_list

def Divide_group(event, x, y, flags, param):
	# grab references to the global variables
	global refPt, cropping,points,z

	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being
	# performed
	
	if event == cv2.EVENT_LBUTTONDOWN:
		refPt = [(x, y)]
		points.append((x,y))
		
		# check to see if the left mouse button was released
	elif event == cv2.EVENT_LBUTTONUP:
		# record the ending (x, y) coordinates and indicate that
		# the cropping operation is finished
		refPt.append((x, y))
		points.append((x,y))
		z=z+1
		

		# draw a rectangle around the region of interest
		cv2.rectangle(image, refPt[0], refPt[1],(0, 255, 0),2)
		cv2.putText(image,"group"+str(z+1),points[2*z],cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
		print(refPt[0], refPt[1])
		print(points)
		cv2.imshow("image", image)
	
		
def returnCSV_custom(fileName,final_group,subject):
	CSVFile=open(fileName,'w')
	CSVFile.write("user,subject,group \n")
	
	for key in final_group:
		for n in final_group[key]:
			CSVFile.write(n+","+subject+","+key+"\n")
		
	CSVFile.close()

def returnCSV_dyanamic(fileName,class_grid,subject,allocated):
	CSVFile=open(fileName,'w')
	CSVFile.write("user,subject,group \n")
	
	for person  in allocated:
		k=(np.sum(np.argwhere(class_grid==person)))%2+1
		CSVFile.write(person+","+subject+",group"+str(k)+"\n")
		
	CSVFile.close()


def group():
	
	subject_name="EN4573"
	final_groups={}

	global refPt, cropping,points,z,image,method,cordinate_dictionary,number_of_groups
	# load the image, clone it, and setup the mouse callback function
	#image = cv2.imread("frame.jpg")
	print(image.shape[:2])

	if (method)=="custom":
		for key in cordinate_dictionary:
			cv2.circle(image, cordinate_dictionary[key], 2,(0, 255, 0),2)	

		clone = image.copy()
		cv2.namedWindow("image")
		cv2.setMouseCallback("image", Divide_group)


		# keep looping until the 'q' key is pressed

		while True:
			if (len(points)<(2*int(number_of_groups)+1)):
			
				cv2.imshow("image", image)
				key = cv2.waitKey(1) & 0xFF

						# if the 'r' key is pressed, reset the cropping region
				if key == ord("r"):
					image = clone.copy()
					points=[]
					z=-1
					print("Reseting group")
			

						# if the 'c' key is pressed, break from the loop
				elif key == ord("c"):
					break
			else:
				print("give only required points")
				break

		for i in range(int(number_of_groups)):
			group_names=check(points[2*i],points[2*i+1],cordinate_dictionary)
			final_groups['group'+str(i+1)] = group_names
		print(final_groups)


		returnCSV_custom("group.csv",final_groups,subject_name)
		
	if (method)=="dynamic":
		cordinate_dictionary["start"]=(0,0)
		allocated=[]
		non_allocated=cordinate_dictionary.keys()
		n= len(cordinate_dictionary)
		class_grid= [[0 for x in range(n)] for y in range(n)]

		non_allocated.remove("start")

		start_person, _ = create_distance("start",non_allocated)
		class_grid[0][0] = start_person
		allocated.append(start_person)
		non_allocated.remove(start_person)
		index_dictionary = {start_person:(0,0)}
		student_number = len(non_allocated)

		for r in range(student_number):
		    source, destination = find_short_neighbour(allocated,non_allocated)
		    degree = angle(cordinate_dictionary[source],cordinate_dictionary[destination])
		    destination_index = place(degree,index_dictionary[source])
		    index_dictionary[destination] = destination_index
		    class_grid[destination_index[1]][destination_index[0]] = destination
		    allocated.append(destination)
		    non_allocated.remove(destination)
		class_grid=np.asarray(class_grid)
		print(class_grid)
	
		returnCSV_dyanamic("group.csv",class_grid,subject_name,allocated)

		#print(angle(cordinate_dictionary["athavan"],cordinate_dictionary["piri"]))


		#degree=angle(cordinate_dictionary[last_allocated],cordinate_dictionary[x])

		#print(x,degree)


		#print(place(degree,(0,0)))	

	cv2.destroyAllWindows()

def dialog1():

    username=entry1.get()
    password = entry2.get()

    if (username == 'EN4553' and  password == 'secret'):
		global window
		window.destroy()
        #box.showinfo('info','Correct Login')
		root=Tk()
		#root.config(background="green")
		#for widget in frame.root():
		#	widget.destroy()
		theLabel=Label(root,text="Vision based Digital Classroom",anchor=CENTER,relief=RIDGE)
		theLabel.config(width=200,font=("Courier", 34),background="green", foreground="blue")
		theLabel.pack(side="top",fill=X)


		canvas = Canvas(root, width = 1200, height = 525)

		canvas.pack(pady=5, padx=10)
		#setup_master(canvas)
		img = ImageTk.PhotoImage(Image.open("ENTC.png"))
		#imshow(img)
		canvas.create_image(25, 10, anchor=NW, image=img)

		topframe=Frame(root,width=50,height=50)
		topframe.pack()

		mainframe=Frame(root,width=50,height=50)
		mainframe.pack(pady = 10, padx = 10)

		mainframe2=Frame(root,width=50,height=50)
		mainframe2.pack(pady = 5, padx = 10)

		button1=Button(topframe,text="Group class",command=group)
		#button1.config(background="blue")
		button2=Button(topframe,text="Attendance")
		#button3=Button(downframe,text="attendance")
		button1.pack(side=LEFT)
		button2.pack(side=BOTTOM)
		#button3.pack(side=BOTTOM)

		# Add a grid
		#mainframe = Frame(root)
		mainframe.grid(column=0,row=0, sticky=(N,W,E,S) )
		mainframe.columnconfigure(0, weight = 1)
		mainframe.rowconfigure(0, weight = 1)
		mainframe.pack(pady = 10, padx = 5)

		# Create a Tkinter variable
		tkvar = StringVar(root)

		# Dictionary with options
		choices = {'custom','dynamic',""}
		tkvar.set('dynamic') # set the default option

		popupMenu = OptionMenu(mainframe, tkvar, *choices)
		Label(mainframe, text="Choose a method").grid(row = 1, column = 1)
		popupMenu.grid(row = 3, column =1)

		##########
		# Add a grid
		#mainframe = Frame(root)
		mainframe2.grid(column=0,row=0, sticky=(N,W,E,S) )
		mainframe2.columnconfigure(0, weight = 1)
		mainframe2.rowconfigure(0, weight = 1)
		mainframe2.pack(pady = 10, padx = 10)

		# Create a Tkinter variable
		tkvar1 = StringVar(root)

		# Dictionary with options
		choices1 = {1,2,3,4}
		#tkvar1.set(1) # set the default option

		popupMenu = OptionMenu(mainframe2, tkvar1, *choices1)
		Label(mainframe2, text="Choose number of groups").grid(row = 1, column = 1)
		popupMenu.grid(row = 3, column =1)

		# on change dropdown value
		def change_dropdown(*args):
			global method,number_of_groups
			method=str(tkvar.get())
			number_of_groups = int(tkvar1.get())
			print(tkvar1.get() )
		#method="custom"
		# link function to change dropdown
		tkvar.trace('w', change_dropdown)
		root.mainloop()
    else:
        box.showinfo('info','Invalid Login')

##SSH Transaction
ssh = createSSHClient("10.12.67.36",22,"madhushanb", "group10@fyp")
scp = SCPClient(ssh.get_transport())

#scp.get('/home/madhushanb/Human_Detection_And_Reid/Dict.txt','/home/harishanth/GIT/Grouping_events/mouse-click-events')
##########

image = cv2.imread("frame.jpg")
file = open('Dict.txt','r')
#cordinate_dictionary=json.loads(file.read())
file.close()
window = Tk()
#global window
window.title('Digital_Classroom')
cordinate_dictionary={"hari":(421,291),"Thiva":(171,289),"nilaki":(371,152),"mad":(102,151),"athavan":(675,186),"piri":(771,283)}

frame = Frame(window)

Label1 = Label(window,text = 'Username:')
Label1.pack(padx=15,pady= 5)

entry1 = Entry(window)
entry1.pack(padx=15, pady=5)

Label2 = Label(window,text = 'Password: ')
Label2.pack(padx = 15,pady=6)

entry2 = Entry(window)
entry2.pack(padx = 15,pady=7)

btn = Button(frame, text = 'Login',command = dialog1)

btn.pack(side = RIGHT , padx =5)
frame.pack(padx=100,pady = 19)
window.mainloop()



