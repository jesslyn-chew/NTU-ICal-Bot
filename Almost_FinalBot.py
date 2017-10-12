#########################################################################
#### NTU ICalendar Bot
# Function: By providing the user course code and class index, the bot will
#           generate an ICalendar
# Steps :
# 1.
# Limitation:
# 1) The bot can only work on this Semester
#Improvements: Working for other modules from other schools (like LG9001)
#########################################################################

import sys
import os
sys.path.append('.')
sys.path.append('../')
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException 
import numpy as np
import csv
from datetime import datetime, timedelta
from convert import Convert

# 1. Naming and Setting Variables
###########################################################################
# Variables for Modules Name,Timetable,index group of every user respectively
ModulesData = []                                    
ModulesName = []                                   
ClassIndexName = []
# List that consists of names of all flags (flag are to ensure code runs in order)
All_flags = ["getCal_flag", "CourseCode_flag", "CheckCourse_flag", "ClassIndex_flag",\
             "ExtraOptions_flag", "Remove_flag", "Generate_flag", "Feedback_flag"]
# Ensure all flags are initialized and empty
for flag in All_flags:
    set_empty = flag + " = []"
    exec (set_empty)


# 2. Telebot Functions A
###########################################################################
# To identify location of the user id(index_UD) in list for ModulesName, ModulesData, ClassIndexName
def UserData(index_UD):
    global ModulesName
    # Start the check from the first row of the list
    counter_UD = 0
    # It is assumed(and is true) that the row number for the user id is the same for the 3 list
    for UserModulesName_UD in ModulesName:
        if UserModulesName_UD[0] == index_UD:
            break
        else:
            # Increment the counter by 1 to check the next row
            counter_UD += 1
    # Return the "row" number for the user id        
    return counter_UD

# Set all flags with a specific chat_id to empty
def reset_flags(index_RS):
    global getCal_flag, CourseCode_flag, CheckCourse_flag, ClassIndex_flag,\
           ExtraOptions_flag, Remove_flag, Generate_flag, Feedback_flag
    index_RS = int(index_RS)
    # Loop for every flag in the All_flag list
    for flag_RS in All_flags:
        # obtain the contents of the flag
        flag_type_RS = eval(flag_RS)
        # if the flag contains the user id, remove it from the flag
        if index_RS in flag_type_RS:
            command_RS = flag_RS + ".remove(index_RS)"
            eval (command_RS)
            
# To remove any data on modules for each user
def reset_data(chat_id_RD):
    global ModulesName, ModulesData, ClassIndexName
    # Obtain the row number in MAIN Lists(ModulesName,ModulesData,ClassIndexName) that contains the user id 
    index_RD = UserData(chat_id_RD)
    if index_RD != len(ModulesName):
        # remove all data, leaving the user id behind 
        del(ModulesName[index_RD][1:])
        del(ModulesData[index_RD][1:])
        del(ClassIndexName[index_RD][1:])
        # For debugging 
        print(ModulesName[index_RD], ModulesData[index_RD], ClassIndexName[index_RD])
    else:
        # if the user id is not present in MAIN lists, add it to MAIN lists as a list
        ModulesName.append([chat_id_RD])
        ModulesData.append([chat_id_RD])
        ClassIndexName.append([chat_id_RD])

# For every message through telegram, it gets filtered out here (according to message type)
def handle(msg):
    global ModulesName, ModulesData, ClassIndexName
    global content_type, chat_type, chat_id, flavor
    global ExtraOptions_markup, return_markup
    # Obtain a brief description of the telegram chat input by users
    flavor = telepot.flavor(msg)
    content_type, chat_type, chat_id = telepot.glance(msg, flavor=flavor)
    # Output the description to the server console 
    summary = (flavor, content_type, chat_type, chat_id )
    print (summary)
    # Creating variables for InlineKeyboard that are used in mutiple steps 
    return_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Return to Settings', callback_data='NONE')]])
    ExtraOptions_markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='Add modules', callback_data='ADD')],
                        [InlineKeyboardButton(text='Remove modules', callback_data='REMOVE')],
                        [InlineKeyboardButton(text='Check modules', callback_data='CHECK')],
                        [InlineKeyboardButton(text='Continue and retrieve ICal', callback_data='CONTINUE')]
                        ])
    # For Debugging and checking variables 
    print (getCal_flag, CourseCode_flag, CheckCourse_flag, ClassIndex_flag,\
           ExtraOptions_flag, Remove_flag, Generate_flag)
    print (ModulesName)
    print (ModulesData)
    print (ClassIndexName)
    # When user input is in text, run on_chat_message(msg)
    if flavor == "chat":
        on_chat_message(msg)
    # When user input is in inlinekeyboard, run on_callbackquery(msg)
    elif flavor == "callback_query":
        on_callback_query(msg)
    else:
        return

def on_chat_message(msg_OCM):
    global getCal_flag, CourseCode_flag, CheckCourse_flag, ClassIndex_flag,\
           ExtraOptions_flag, Remove_flag, Generate_flag, Feedback_flag
    global ModulesName, ModulesData, ClassIndexName
    
    #Step 0: "/start" command to introduce bot to user
    if msg_OCM["text"] == "/start":
        bot.sendMessage(chat_id, """ Hello there! I am ICalBot, and I am here to simplify your life in NTU.
You can use me to retrieve an electronic calendar for Your Modules (You will need to give me your course code and group index) or NTU Key Events. 
May TheForce be with you.

To begin, click /getCal
click /help for more information """)
        reset_flags(chat_id)
        # Create "storage" space for the input/output for each user
        reset_data(chat_id)

    #Step 1: "/getCal" command for options of ICal: for Specific Courses or NTU Key Events
    elif msg_OCM["text"] == "/getCal":
        getCal_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Get ICal for Specific Course(s)', callback_data='Course')],
            [InlineKeyboardButton(text='Get ICal for NTU Key Events', callback_data='NTUEvent')]
            ])
        message_with_inline_keyboard = bot.sendMessage(chat_id, "Which ICal would you like to generate?", reply_markup=getCal_markup)
        getCal_flag.append(chat_id)
        
    #Step -1: "/reset" command to reset data and values
    elif msg_OCM["text"] == "/reset":
        bot.sendMessage(chat_id, "All data has been reset. Please type /getCal if you would like to begin once again")
        reset_data(chat_id)
        reset_flags(chat_id)
        
    #Step -2: "/help" to provide more commands
    elif msg_OCM["text"] == "/help":
        bot.sendMessage(chat_id, """ NTU_ICal_Bot is pretty easy to use, just follow the instructions!

Type /getCal if you would like to obtain an ICal
Type /reset if you accidentally end up the wrong place AND would like to remove all modules
Type /feedback if you have any remarks on the bot""")

    #Step -3: "/feedback" for user remarks
    elif msg_OCM["text"] == "/feedback":
        bot.sendMessage(chat_id, "What would you like to feedback on?")
        Feedback_flag.append(chat_id)

    elif chat_id in Feedback_flag:
        bot.sendMessage(chat_id, "Thank you for your feedback :)")
        # Feedback will be transfered to one of the teammates telegram account
        bot.sendMessage(264983884, msg_OCM["text"])
        Feedback_flag.remove(chat_id)
        
    #Step 3: After receiving Course Code, check whether the retrieved data is correct
    elif chat_id in CourseCode_flag:
        bot.sendMessage(chat_id, "Please wait for moment, this may take awhile...")
        CourseInput_3 = msg_OCM["text"]
        # Obtain relevant data from selenium
        Retrieved_Course_3 = timetable_extract(CourseInput_3,chat_id)
        # the course code does not exist, user either input a different course or return to settings
        if Retrieved_Course_3 == False:
            bot.sendMessage(chat_id, "Can't find your course. Please retry: ", reply_markup=return_markup)
            reset_flags(chat_id)
            Remove_flag.append(chat_id)
            CourseCode_flag.append(chat_id)
        # the course code exist but it is an online course, user either input a different course or return to settings
        elif Retrieved_Course_3 == True:
            bot.sendMessage(chat_id, """This module is an online course, thus there is no input for the timetable(aren't you glad).
Please select another module:""", reply_markup=return_markup)
            reset_flags(chat_id)
            Remove_flag.append(chat_id)
            CourseCode_flag.append(chat_id)
        # course code exist, get user confirmation that the course is correct
        else:
            bot.sendMessage(chat_id, Retrieved_Course_3)
            bot.sendPhoto(chat_id, open('class_index.png', 'rb'))
            YesNo_markup = InlineKeyboardMarkup (inline_keyboard=[
                [InlineKeyboardButton(text='Yes', callback_data='Y')],
                [InlineKeyboardButton(text='No', callback_data='N')]
                ])
            bot.sendMessage(chat_id, "Is this the course you are looking for? (Yes/No)", reply_markup=YesNo_markup)
            reset_flags(chat_id)
            CheckCourse_flag.append(chat_id)


    #Step 5: After class index input, get timetable and extra options(Add,Remove,Output)
    elif chat_id in ClassIndex_flag:
        ClassInput = msg_OCM["text"]
        index_5 = UserData(chat_id)
        # Obtain data of the latest module 
        List_5 = ModulesData[index_5][-1]   
        print (List_5)
        Result_5 = timetable_extract2(List_5, ClassInput, chat_id)
        # Classindex exist, add updated data to MAIN lists for user
        if Result_5 == True:
            bot.sendMessage(chat_id, (ModulesName[index_5][-1] + " Added."))
            bot.sendMessage(chat_id, "Would you like to:", reply_markup=ExtraOptions_markup)
            ClassIndexName[index_5].append(ClassInput)
            # For debugging 
            print (ModulesData,ModulesName,ClassIndexName)
            reset_flags(chat_id)
            ExtraOptions_flag.append(chat_id)
        # Classindex do not exist, user have to input another class index
        else:
            bot.sendMessage(chat_id, "Can't find your class index. Please retry: ")
            reset_flags(chat_id)
            ClassIndex_flag.append(chat_id)

def on_callback_query(msg_OCQ):
    global getCal_flag, CourseCode_flag, CheckCourse_flag, ClassIndex_flag,\
           ExtraOptions_flag, Remove_flag, Generate_flag, Feedback_flag
    global ModulesName, ModulesData, ClassIndexName

    if chat_type in getCal_flag:
    #Step 2a: Choosing option for getting course ICal => input CourseCode
        if chat_id == "Course":
            bot.sendMessage(chat_type, "Please enter your course code/name:")
            reset_flags(chat_type)
            CourseCode_flag.append(int(chat_type))
        
    #Step 2b: Choosing option for getting ntu general ICal [End]
        elif chat_id == "NTUEvent":
            bot.sendMessage(chat_type, """All ICal for NTU Key Events are available on this website:
http://www.ntu.edu.sg/Students/Undergraduate/AcademicServices/AcademicCalendar/Pages/AY2016-17.aspx """)

    elif chat_type in CheckCourse_flag:
        #Step 4a: If course is correct, get class index input
        if chat_id == "Y":
            bot.sendMessage(chat_type, "Please enter your class index:")
            reset_flags(chat_type)
            ClassIndex_flag.append(int(chat_type))

        #Step 4b: IF course is wrong, get another course input from user    
        if chat_id == "N":
            bot.sendMessage(chat_type, "Please enter your CORRECT course code:")
            index_4b = UserData(chat_type)
            # Remove latest CourseName and CourseData from Main lists
            del(ModulesName[index_4b][-1])  
            del(ModulesData[index_4b][-1])
            reset_flags(chat_type)
            CourseCode_flag.append(int(chat_type))

    elif chat_type in ExtraOptions_flag:
        #Step 6a: ADD more modules
        if chat_id == "ADD":
            # User either input course code or return to settings
            bot.sendMessage(chat_type, "Please enter your course code/name:",reply_markup=return_markup)
            reset_flags(chat_type)
            Remove_flag.append(int(chat_type))
            CourseCode_flag.append(int(chat_type))

        #Step 6b: REMOVE modules
        if chat_id == "REMOVE":
            # inlinekeyboard for return option
            markup_code = "InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Return', callback_data='NONE')],"
            # Location of first Module Name in the row 
            modulecounter_6b = 1
            index_6b = UserData(chat_type)
            Modules_6b = ModulesName[index_6b]
            # For each Module Name, form portion of the code 
            for Module_6b in Modules_6b[1:]:
                code_segment = '[InlineKeyboardButton(text="""{}""", callback_data="{}")],'.format(Module_6b,modulecounter_6b)
                markup_code = markup_code + code_segment
                modulecounter_6b += 1
            # Complete the code (Parentheses)
            markup_code = markup_code[:-1] + "])"
            markup_code = eval (markup_code)
            bot.sendMessage(chat_type, "Which module would you like to remove?", reply_markup=markup_code)
            reset_flags(chat_type)
            Remove_flag.append(int(chat_type))

        #Step 6c: Check Modules in list    
        if chat_id == "CHECK":
            # Obtain the row number in which the user's modules are located
            index_6c = UserData(chat_type)
            # Obtain the last index of the last module in the row 
            ModuleNumber_6c = len(ModulesName[index_6c]) - 1
            # if there are no modules added, inform the user (Where the user id is only present)
            if ModuleNumber_6c == 0:
                bot.sendMessage(chat_type, "No modules added.")
            # if there are modules added, inform the user of its course code and group index
            else:
                for N in range(0,ModuleNumber_6c):
                    bot.sendMessage(chat_type, ("{} [Group index:{}]".format(ModulesName[index_6c][N+1],ClassIndexName[index_6c][N+1])))
            bot.sendMessage(chat_type, "Would you like to:", reply_markup=ExtraOptions_markup)
                    
        #Step6d : Export ICal
        if chat_id == "CONTINUE":
            bot.sendMessage(chat_type, "Please wait for moment, this may take awhile...")
            # Obtain location of data of modules for the user 
            index_6d = UserData(chat_type)
            # Generate the ICal
            ICal_Generator(ModulesData[index_6d][1:],ModulesName[index_6d][1:],chat_type)
            # Send the ICal doc (Specific to chat_id)
            bot.sendDocument(chat_type, open("calendar" + str(chat_type)+".ics"))
            bot.sendMessage(chat_type, """Here is the ICal you wanted! If you want to obtain a different ICal, click or type /getCal""")
            # Reset or remove previous data left by user
            reset_flags(chat_type)
            reset_data(chat_type)
            os.remove("calendar" + str(chat_type)+".ics")
            os.remove("calendar" + str(chat_type)+".csv")


    #Step6bi : After Remove Module   
    elif chat_type in Remove_flag:
        # if the user choose not to remove the data return to the settings menu
        if chat_id == "NONE":
            bot.sendMessage(chat_type, "Would you like to:", reply_markup=ExtraOptions_markup)
            reset_flags(chat_type)
            ExtraOptions_flag.append(int(chat_type))
        # if user wants to remove a module
        else:
            # mod_number represents the column no. of where the module is located in MAIN lists
            mod_number = int(chat_id)
            index_6bi = UserData(chat_type)
            bot.sendMessage(chat_type, (ModulesName[index_6bi][mod_number] + " Removed."))
            # remove data from MAIN lists
            del(ModulesData[index_6bi][mod_number])
            del(ModulesName[index_6bi][mod_number])
            del(ClassIndexName[index_6bi][mod_number])
            # Return to settings
            bot.sendMessage(chat_type, 'Would you like to:', reply_markup=ExtraOptions_markup)
            reset_flags(chat_type)
            ExtraOptions_flag.append(int(chat_type))


# 3. Selenium Function
################################################################################################
#Step 3: Retrieve Course Timetable with selenium
def timetable_extract(Courseinput, chat_id_TE1):
    # Problem 1: driver not working (Issue of path of driver)
    # Run driver (on Chrome or by phantomJS)
    driver = webdriver.Chrome()
    # Ensure that the driver is fully loaded
    driver.implicitly_wait(5)
    # Move to the NTU website for extraction of modules
    driver.get("https://wish.wis.ntu.edu.sg/webexe/owa/aus_schedule.main")

    # To check that the webpage is correct
    #@@@@assert "Class Schedule" in driver.title@@@@@@@@@           

    # Find the element for inputting course code
    Keyword_TE1 = driver.find_element_by_name("r_subj_code")
    # Input the user's course code to the element found
    Keyword_TE1.send_keys(Courseinput)
    # Find and select the "Enter" button
    driver.find_element_by_xpath('//input[4]').click()                     
    # Problem 2: Enter the values was an issue, button was assigned an input value so cannot use 'select'

    # Switching Tabs:
    #Slow computer problem
    driver.implicitly_wait(5)
    # Get list for all tab names
    tabs_TE1 = driver.window_handles                                           
    # Switch to last created tab
    driver.switch_to_window(tabs_TE1[-1])                                        
    #print (driver.current_url)                                             
    driver.save_screenshot('class_index.png')
    # Check the focus tab is correct
    #@@@@@assert "Class Schedule" in driver.title@@@@@@@
    try:
        # Obtain and merge the course code and name by using xpath
        Retrieved_Course1_TE1 = driver.find_element_by_xpath("/html/body/center/table[1]/tbody/tr[1]/td[1]/b/font")
        Retrieved_Course2_TE1 = driver.find_element_by_xpath("/html/body/center/table[1]/tbody/tr[1]/td[2]/b/font")
        Retrieved_Course_TE1 = (Retrieved_Course1_TE1.text) + " " + (Retrieved_Course2_TE1.text)

        # Create an empty list 
        Alltext_TE1 = []
        # Find element of "INDEX, TYPE, GROUP, DAY, TIME, VENUE, REMARK" category 
        tablecontents_TE1 = driver.find_elements_by_xpath("/html/body/center/table[2]/tbody/tr/td")

        for elements_TE1 in tablecontents_TE1:
            # Convert each element to text form and input to an array
            elements_TE1 = elements_TE1.text
            Alltext_TE1.append(elements_TE1)
        # For debugging (Ensure the list is correct)
        print(Alltext_TE1)

        # Filter out Online Courses
        if Alltext_TE1[6] == "Online Course":
            driver.quit()
            return True
        
        else:
            # Add course data/name to MAIN LIST (subset list with user id) 
            counter_TE1 = UserData(chat_id_TE1)  
            ModulesData[counter_TE1].append(Alltext_TE1)
            ModulesName[counter_TE1].append(Retrieved_Course_TE1)

            # End selenium program
            driver.quit()
            return Retrieved_Course_TE1
    except:
        driver.quit()
        return False
    
def timetable_extract2(Alltext_TE2,Classinput_TE2,chat_id_TE2):
    global ModulesData, ModulesName
    # Find the total no.. of elements in the list
    length_TE2 = len(Alltext_TE2)
    # Find the total no. of rows if there were 7 columns 
    subsetno_TE2 = length_TE2 / 7
    Alltext_TE2 = np.array(Alltext_TE2)
    # Create a "table" format of x rows and 7 columns
    Table_TE2 = Alltext_TE2.reshape(int(subsetno_TE2),7)
    # Create an empty set for valid rows only, aka "newlist"
    newlist_TE2 = []
    newlist_2_TE2 = []
    try:
        # filter top half
        for row_TE2 in Table_TE2:
            if (row_TE2[0] != Classinput_TE2):
                Table_TE2 = np.delete(Table_TE2,[0],0)
            elif (row_TE2[0] == Classinput_TE2):
                break

        # Move the first row to "newlist"
        newlist_TE2.append(Table_TE2[0])

        # filter bottom half
        for row_TE2 in Table_TE2[1:]:
            # If first column of each row is empty, then carry out:
            if (row_TE2[0] == ""):
                # Move row to "newlist"
                newlist_TE2.append(row_TE2)
            # If first colum is not empty, stop loop
            elif (row_TE2[0] != ""):
                break   
        # Change time format from "1030-1130" to "10:30","11:30"
        for rows_TE2 in newlist_TE2:
            rows_TE2[0] = newlist_TE2[0][0]
            TIME_TE2 = rows_TE2[4]
            
            TIME_TE2 = TIME_TE2.split("-")
            StartTime_TE2 = TIME_TE2[0]
            StartTime_TE2 = str(StartTime_TE2[0:2]) + ":" + str(StartTime_TE2[2:4])
            EndTime_TE2 = TIME_TE2[1]
            EndTime_TE2 = str(EndTime_TE2[0:2]) + ":" + str(EndTime_TE2[2:4])

            rows_TE2 = np.delete(rows_TE2, 4)
            rows_TE2 = np.insert(rows_TE2, 4, EndTime_TE2)
            rows_TE2 = np.insert(rows_TE2, 4, StartTime_TE2)
            newlist_2_TE2.append(rows_TE2)

        # For Debugging (newlist is correct)
        #print(newlist_2_TE2)
        index_TE2 = UserData(chat_id_TE2)
        del(ModulesData[index_TE2][-1])
        ModulesData[index_TE2].append(newlist_2_TE2)
        return True

    # Filter wrong input of Course Code
    except:
        return False


# 4. ICAL Generator
#################################################################################################################
def ICal_Generator(finallist_Ical, finalname_Ical, chat_type_Ical):
    #open calendar.csv file
    with open("calendar" + str(chat_type_Ical)+".csv", "w") as c:
        headers_Ical = ("Subject", "StartDate", "StartTime", "EndDate", "EndTime", "AllDayEvent", "Location","Description")
        writer_Ical = csv.DictWriter(c, fieldnames = headers_Ical)
        writer_Ical.writeheader()
        # counter_Ical is to track the location of module NAME
        counter_Ical = -1                    
        # For each module added by the user
        for Module_Ical in finallist_Ical:
            counter_Ical += 1

            #write data into calendar.csv file
            for row_Ical in Module_Ical:
                #define variables here
                First_monday_Ical = "14/8/2017" #supposed to be input value from telegram
                dates_list_Ical = []
                subject_Ical = finalname_Ical[counter_Ical] + " {}".format(row_Ical[1])          #subject located at this current row and first column
                starttime_Ical = row_Ical[4]                                                     #start time located at this current row and column 5th
                endtime_Ical = row_Ical[5]                                                       #end time located at this current row and column 6th
                alldayevent_Ical = "False"                                                       #all day event is set to false
                description_Ical = " Group: %s \n %s" %(row_Ical[2],row_Ical[7])                 #type of lession and group number is located at 2nd, 3rd, 8th column
                location_Ical = row_Ical[6]                                                      #location located at this current row and 7th column
                
                #----assigning values to days of wk and changing date accordingly ----#  
                if(row_Ical[3] == str("MON")):
                    b = 0
                    date_Ical = datetime.strptime(First_monday_Ical,'%d/%m/%Y') + timedelta(days=b)
                    date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))
    
                elif(row_Ical[3] == str("TUE")):
                    b = 1
                    date_Ical = datetime.strptime(First_monday_Ical,'%d/%m/%Y') + timedelta(days=b)
                    date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))

                elif(row_Ical[3] == str("WED")):
                    b = 2
                    date_Ical = datetime.strptime(First_monday_Ical,'%d/%m/%Y') + timedelta(days=b)
                    date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))

                elif(row_Ical[3] == str("THU")):
                    b = 3
                    date_Ical = datetime.strptime(First_monday_Ical,'%d/%m/%Y') + timedelta(days=b)
                    date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))
                
                elif(row_Ical[3] == str("FRI")):
                    b = 4
                    date_Ical = datetime.strptime(First_monday_Ical,'%d/%m/%Y') + timedelta(days=b)
                    date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))

                elif(row_Ical[3] == str("SAT")):
                    b = 5
                    date_Ical = datetime.strptime(First_monday_Ical,'%d/%m/%Y') + timedelta(days=b)
                    date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))

                #----while loop to print/insert all possible dates into array----#
                wk_segment_Ical = row_Ical[7]
                if wk_segment_Ical == "":
                    total_wk_Ical = range(0,13)
                else:
                    # Recall in this code, value wk 0 is representing actual wk 1 and wk cap is 12
                    total_wk_Ical = []                                   # To input the int value of week with lesson
                    wk_segment_Ical = wk_segment_Ical.replace("Wk","")        # Remove the "Wk" in the string
                    wk_segment_Ical = wk_segment_Ical.split(",")
                    for segment_counter_Ical in range(0,len(wk_segment_Ical)):
                        if "-" in wk_segment_Ical[segment_counter_Ical]:
                            segment_Ical = wk_segment_Ical[segment_counter_Ical].split("-")
                            start_segment_Ical = int(segment_Ical[0]) - 1
                            end_segment_Ical = int(segment_Ical[1])
                            range_Ical = range(start_segment_Ical,end_segment_Ical)                                
                            for each_wk_Ical in range_Ical:
                                total_wk_Ical.append((each_wk_Ical))
                        else:
                            total_wk_Ical.append((int(wk_segment_Ical[segment_counter_Ical]))-1)

                print("POTATO")
                print(total_wk_Ical)
                 
                for wk_Ical in range(0,13):
                    if(wk_Ical != 6):
                        if wk_Ical in total_wk_Ical:
                            dates_list_Ical.append(date_Ical)
                            print(dates_list_Ical)
                        date_Ical = datetime.strptime(date_Ical,'%m/%d/%Y') + timedelta(days=7)
                        date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))

                    else:
                        if wk_Ical in total_wk_Ical:
                            dates_list_Ical.append(date_Ical)
                            print(dates_list_Ical)
                        date_Ical = datetime.strptime(date_Ical,'%m/%d/%Y') + timedelta(days=14)
                        date_Ical = str(datetime.strftime(date_Ical, '%m/%d/%Y'))
        
                    #----while loop to print/insert all possible dates into array----#
                for dcol_Ical in range(0,len(total_wk_Ical)):
                    start_end_date_Ical = dates_list_Ical[dcol_Ical]
                    writer_Ical.writerow({"Subject" : subject_Ical, "StartDate" : start_end_date_Ical , "StartTime" : starttime_Ical , \
                                     "EndDate" : start_end_date_Ical , "EndTime" : endtime_Ical , "AllDayEvent" : alldayevent_Ical , \
                                     "Description" : description_Ical, "Location" : location_Ical})

    #Initializing Converter for CSV to ICS file,
    #each variable equivalent to a column in the csv file generated
    convert = Convert()
    convert.CSV_FILE_LOCATION = "calendar" + str(chat_type_Ical)+".csv"
    convert.SAVE_LOCATION = "calendar" + str(chat_type_Ical)+".ics"
    convert.HEADER_COLUMNS_TO_SKIP = 0

    convert.NAME = 0
    convert.START_DATE = 1
    convert.END_DATE = 2
    convert.DESCRIPTION = 7
    convert.LOCATION = 6

    CSV_Data = convert.csv_data
    # Create a list for data in csv
    convert.read_csv()
    # convert.csv_data is the returned value(list) of convert.read_csv

    # To remove headings
    i = 1
    while i < (len(CSV_Data)):
        CSV_Row = CSV_Data[i]
        print(CSV_Row)
        if CSV_Row != []:
            # Order should be [EVENTNAME, START_DATE, END_DATE, DESCRIPTION, LOCATION]
            CSVstart_date = str(CSV_Row[1]) + '-'+ str(CSV_Row[2])
            CSVend_date = str(CSV_Row[3]) + '-' + str(CSV_Row[4])
            CSV_Data[i][convert.START_DATE] = datetime.strptime(CSVstart_date, '%m/%d/%Y-%H:%M')
            CSV_Data[i][convert.END_DATE]= datetime.strptime(CSVend_date, '%m/%d/%Y-%H:%M')
            i +=1
            print("added")
        else:
            CSV_Data.pop(i)
            # For Debugging
            #print(CSV_Data)
            
    convert.csv_data = CSV_Data[1:]
    print(convert.csv_data)
    convert.make_ical()
    #print (convert.cal)                        #Debug check for ical file
    convert.save_ical()
    


# Telebot Function 2
################################################################################################
# Token from command line
Token = "448731944:AAE11-w80lMnPKt12oxorPFX5gdFFaKpQ0c"
bot = telepot.Bot(Token)
# run the code with a new telegram message is received
MessageLoop(bot, handle).run_as_thread()

print ('Listening ...')

# Keep the program running
while 1:
    time.sleep(10)
            
