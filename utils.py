from datetime import datetime, timedelta, date
import pandas as pd

def fix_time(time_start,current_time):
    """This function fixes the timestamps used by converting them to seconds, starting at zero.
    
    Args:
        time_start (str): The time at which the first action was done.
        current_time (str): The current time we are converting.

    Returns:
        current_time_fixed: The time of the current action converted into seconds given that the first action was done as 0 seconds.
    """
    #check that the current time is later than first time stamp
    if datetime.combine(date.min, current_time) >= datetime.combine(date.min, time_start):
        current_time_fixed = (datetime.combine(date.min, current_time) - datetime.combine(date.min, time_start)).total_seconds()
    else:
        #ex: this is the case when time_start is 59:00 min and cuurent_time is 02:00 min, so we add an hour to find the duration in between
        current_time_fixed = (datetime.combine(date.min, current_time) + timedelta(hours=1) - datetime.combine(date.min, time_start)).total_seconds()
    return current_time_fixed

def get_duration(row):
    """This function gets the duration of an action given the difference in time
    between the current and next timestamp.
    
    Args:
        row (Pandas element): The row of the action for which we want to find the duration.

    Returns:
        duration: The difference in time in seconds between the Timeshifted and Time variables.
    """
    if pd.notnull(row['Timeshifted']): #check that this is not the last action which will have a NA Timeshifted value
        #check that the time of the next action is indeed later than time of the current actin
        if datetime.combine(date.min, row['Timeshifted']) >= datetime.combine(date.min, row['Time']):
            duration = (datetime.combine(date.min, row['Timeshifted']) - datetime.combine(date.min, row['Time'])).total_seconds()
        else:
            #ex: this is the case when TimeSHifted is 59:00 min and Time is 02:00 min, so we add an hour to find the duration in between
            duration = (datetime.combine(date.min, row['Timeshifted']) + timedelta(hours=1) - datetime.combine(date.min, row['Time'])).total_seconds()
    else:
        duration = 10 #last action lasts zero seconds but we need to put a dummy variable here.
    return duration

def clean_method(method):
    return method.replace("}","").replace("{","").replace("x -",'')
    
def get_action_usage(df,column,action):
    '''Given an action or method, we detect its use using a particular column
    and then extract a list of time coordinates for when
    they were used. These coordinates are in the format (start_time, duration)
    
    Args:
        df (Pandas dataframe): The dataframe to search in.
        column (str): The column where the method or action might be logged.
        action (str): The name of the action or method to search for in the column.
        

    Returns:
        A list of tuples with start times of the action and it's duration [(start1,duration1),(start2,duration2),...]
    '''
    return zip(df[df[column].str.contains(action,na=False)]['Time_seconds'],df[df[column].str.contains(action,na=False)]['Duration'])

def get_action_usage_exact(df,column,action):
    '''Given an action or method, we detect its use using a particular column
    and then extract a list of time coordinates for when
    they were used. These coordinates are in the format (start_time, duration)
    
    Args:
        df (Pandas dataframe): The dataframe to search in.
        column (str): The column where the method or action might be logged.
        action (str): The name of the action or method to search for in the column.
        

    Returns:
        A list of tuples with start times of the action and it's duration [(start1,duration1),(start2,duration2),...]
    '''
    return zip(df[df[column].str.match(action,na=False)]['Time_seconds'],df[df[column].str.match(action,na=False)]['Duration'])

def merge_action_usage(x,y):
    '''
    Given two lists of coordinates, we merged them and return the new coordinates.
    These coordinates are in the format (start_time, duration)
    
    Args:
        x (list): One set of coordinates
        y (list): A second set of coordinates

    Returns:
        A list of tuples with merged start and duration coordinates [(start1,duration1),(start2,duration2),...]
        
    For example:
        x = [(0,1),(2,3),(10,3)] #0,2,3,4,10,11,12
        y = [(0,2),(3,1),(9,2),(12,2)] #0,1,3,9,10,12,13
        then merged(x,y) => [(0, 2), (2, 3), (9, 5)] #0,1,2,3,4,9,10,11,12,13

    '''
    
    x.extend(y) #we put all the coordinates in one list
    x.sort() #sort them by start time
    merged = []
    
    #for pairs of coordinates, we check if we can merged them
    for i,(s1,d1) in enumerate(x):
        if i != len(x)-1: 
            s2,d2 = x[i+1] #get next coordinates
            if s1 == s2: #if same start times, find max duration
                merged.append((s1,max(d1,d2)))
                x.remove((s2,d2))
            elif s1+d1 >= s2+d2: #if one coordinate bounds the other
                merged.append((s1,d1)) #we add that coordinate
                x.remove((s2,d2)) #and remove the other
            elif s1+d1 >= s2: # if they overlap
                new_duration = d2 + s2-s1 #we calculate a new duration
                merged.append((s1,new_duration)) #add the new coordinate with earliest start time
                x.remove((s2,d2)) #and remove the other
            else:
                merged.append((s1,d1))
        else:
            #these are the last coordinates of x and haven't been merged yet, 
            # so we try to merge them with the previous coordinates
            if s1 <= merged[-1][0]+merged[-1][1]:
                new_start = merged[-1][0]
                new_duration = d1 + s1 - merged[-1][0]
                merged[-1] = (new_start,new_duration) #extend the duration of the last coordinate
    return merged