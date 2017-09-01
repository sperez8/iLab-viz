from datetime import datetime, timedelta, date
from pandas import notnull
import re

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

def calculate_duration(row):
    """This function gets the duration of an action given the difference in time
    between the current and next timestamp.
    
    Args:
        row (Pandas element): The row of the action for which we want to find the duration.

    Returns:
        duration: The difference in time in seconds between the Timeshifted and Time variables.
    """
    if notnull(row['Timeshifted']): #check that this is not the last action which will have a NA Timeshifted value
        #check that the time of the next action is indeed later than time of the current actin
        if datetime.combine(date.min, row['Timeshifted']) >= datetime.combine(date.min, row['Time']):
            duration = (datetime.combine(date.min, row['Timeshifted']) - datetime.combine(date.min, row['Time'])).total_seconds()
        else:
            #ex: this is the case when TimeSHifted is 59:00 min and Time is 02:00 min, so we add an hour to find the duration in between
            duration = (datetime.combine(date.min, row['Timeshifted']) + timedelta(hours=1) - datetime.combine(date.min, row['Time'])).total_seconds()
    else:
        duration = 10 #last action lasts zero seconds but we need to put a dummy variable here.
    return duration

opt_combos3 = {'none choose... all':'all',
          'none all choose...':'choose...',
          'all choose... none':'none',
          'all none choose...':'choose...',
          'choose... none all':'all',
          'choose... all none':'none',
          'all all all':'all',
          'none none none':'none',
          'choose... choose... choose...':'choose...'}

opt_combos2 = {'none all':'all',
          'none choose...':'choose...',
          'all none':'none',
          'all choose...':'choose...',
          'choose... all':'all',
          'choose... none':'none',
          'all all':'all',
          'choose... choose...':'choose...',
          'none none':'none'}

symbol_combos3 = {'x - +' : '+','x - /' : '/','x + -' : '-','x + /' : '/','x / -' : '-','x / +' : '+','- x +' : '+','- x /' : '/','- + x' : 'x','- + /' : '/','- / x' : 'x','- / +' : '+','+ x -' : '-','+ x /' : '/','+ - x' : 'x','+ - /' : '/','+ / x' : 'x','+ / -' : '-','/ x -' : '-','/ x +' : '+','/ - x' : 'x','/ - +' : '+','/ + x' : 'x','/ + -' : '-','- - -':'-','+ + +':'+','/ / /':'/','x x x':'x'}
symbol_combos2 = {'x -' : '-','x +' : '+','x /' : '/','- x' : 'x','- +' : '+','- /' : '/','+ x' : 'x','+ -' : '-','+ /' : '/','/ x' : 'x','/ -' : '-','/ +' : '+','- -' : '-','+ +' : '+','/ /' : '/','x x' : 'x'}

functions_combos2 = {"Average Average":"Average",
                        "Sum Sum":"Sum",
                        "Count Count":"Count",
                        "Median Median":"Median",
                        "Average Sum":"Average",
                        "Sum Sum":"Sum",
                        "Count Sum":"Count",
                        "Median Sum":"Median",
                        "Average Average":"Average",
                        "Sum Average":"Average",
                        "Count Average":"Average",
                        "Median Average":"Average",
                        "Average Count":"Count",
                        "Sum Count":"Count",
                        "Count Count":"Count",
                        "Median Count":"Count",
                        "Average Median":"Median",
                        "Sum Median":"Median",
                        "Count Median":"Median",
                        "Median Median":"Median"}

def clean_method(method):
    method = method.replace("}","").replace("{","").replace("Use","")
    method = re.sub(' +',' ',method) #remove extra spaces
    for combo,replacement in opt_combos3.items():
        method = method.replace(combo,replacement)
    for combo,replacement in opt_combos2.items():
        method = method.replace(combo,replacement)
    for combo,replacement in symbol_combos3.items():
        method = method.replace(combo,replacement)
    for combo,replacement in symbol_combos2.items():
        method = method.replace(combo,replacement)
    for combo,replacement in functions_combos2.items():
        method = method.replace(combo,replacement)
    return method
    
def clean_coords(coords_brocken_up):
    #since the coordinates all subsequent in time, we want to merge them to clean them up.
    #For example:
    # coords_brocken_up = [(0,2),(2,5),(7,2)]
    # coords -> [(0,9)]
    while True:
        coords = merge_usage(coords_brocken_up,coords_brocken_up)
        if coords == coords_brocken_up:
            return coords
        else:
            coords_brocken_up = coords


#Using the example used for sketch.
def prepare_session(df,sessionid):
    new_df = df[df['Session Id'] == sessionid]
    
#     Next we filter out all actions with "INCORRECT" outcomes
    before = new_df.shape[0]
    new_df = new_df[new_df['Outcome'] == 'CORRECT']
    print "After removin 'incorrect' actions, we are left with {0} rows out of {1}".format(new_df.shape[0],before)
    
#     We also clean up the methods removing annoying characters like "{"
    new_df['Cleaned method 1'] = new_df[['Method_Recognized_1_Copied']].applymap(lambda method:clean_method(method))
    new_df['Cleaned method 2'] = new_df[['Method_Recognized_2_Copied']].applymap(lambda method:clean_method(method))

#     We create a column with the data for the contrasting cases
    new_df['cases'] = new_df['CF(new1)'].str.replace('"','') +','+ new_df['CF(new2)'].str.replace('"','')
    
#     Next we fix the time logs and convert them to seconds. We also recalculate the time between actions now that we have gotten rid of incorrect actions.
    time_start = list(new_df['time first action'])[0]
    new_df['Time_seconds'] = new_df[['Time']].applymap(lambda current_time: fix_time(time_start,current_time))
    new_df['Timeshifted'] = new_df[['Time']].shift(-1)
    new_df['Duration'] = new_df[['Time','Timeshifted']].apply(calculate_duration, axis=1)
    return new_df


def action_usage(df,column,action):
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

def action_usage_exact(df,column,action):
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
    return zip(df[df[column].str.match(action,as_indexer=True)]['Time_seconds'],df[df[column].str.match(action,as_indexer=True)]['Duration'])

def merge_usage(x,y):
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
    
    x = x+y #we put all the coordinates in one list
    
    x = list(set(x)) #remove duplicate coordinates
    x.sort() #sort them by start time
    
    if len(x)==1:
        return x
    
    merged = []
    
    
    #for pairs of coordinates, we check if we can merged them
    for i,(s1,d1) in enumerate(x):
        if i != len(x)-1: 
            s2,d2 = x[i+1] #get next coordinates
#             print s1,d1,s2,d2
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
            else: #if it fails, then there is no overlap and we merge them
                merged.append((s1,d1))
    return merged

def intersect_usage(x,y):
    '''
    Given two lists of coordinates, we find the intersect of comon time coordinates and return the new coordinates.
    These coordinates are in the format (start_time, duration)
    
    Args:
        x (list): One set of coordinates
        y (list): A second set of coordinates

    Returns:
        A list of tuples with a intersect of start and duration coordinates [(start1,duration1),(start2,duration2),...]
        
    For example:
        x = [(0,1),(2,3),(10,3)] #0,2,3,4,10,11,12
        y = [(0,2),(3,1),(9,2),(12,2)] #0,1,3,9,10,12,13
        then intersect_usage(x,y) -> [(0, 1), (3, 1), (10, 1), (12, 1)] #0,3,10,12

    '''
    x.sort() #sort them by start time
    y.sort()
    intersect = []
    
    #for pairs of coordinates, we check if we can capture intersect
    while len(x) > 0 and len(y) > 0:
        (sx,dx) = x[0]
        (sy,dy) = y[0]

        if sx == sy: #if same start times, find min duration
            intersect.append((sx,min(dx,dy)))
            if dx<dy:
                x.pop(0)
            else:
                y.pop(0)             
        elif sx < sy and sx+dx > sy: # if they overlap
            if sx+dx >= sy+dy: #if one coordinate bounds the other
                intersect.append((sy,dy)) #we add that inner coordinate
                y.pop(0) #and remove it
            else: #if no bounding, then just overlap
                intersect.append((sy,dx - (sy-sx))) #add the new coordinate with latest start time
                x.pop(0) #and remove the earliest one
        elif sy < sx and sy+dy > sx: # if they overlap (opposite scenario)
            if sy+dy >= sx+dx: #if one coordinate bounds the other (opposite scenario)
                intersect.append((sx,dx)) #we add that inner coordinate
                x.pop(0) #and remove it
            else:
                intersect.append((sx,dy - (sx-sy))) #add the new coordinate with latest start time
                y.pop(0) #and remove the earliest one
        else:
            #there was no intersect so we remove the earliest coordinate
            if sx < sy:
                x.pop(0)
            else:
                y.pop(0)

    return intersect

def merge_method_usage(df, pattern):
    m1 = action_usage_exact(df,'Cleaned method 1',pattern)
    m2 = action_usage_exact(df,'Cleaned method 2',pattern)
    return merge_usage(m1,m2)

def all_cases(df):
    '''Given a dataframe with students' activity, we extract all
    the contrasting cases they were given as well as starting time and
    length of time for which they were working on that case.
    
    Args:
        df (Pandas dataframe): The dataframe to search in.        

    Returns:
        coordinates: a dictionary where the keys are the cases and values are time coordinates.
                    Cases are in the format ('1 2 3 6','2 3 6 7').
                    Time coordinates are in the format (start_time, duration)
    '''
    coordinates = {}
    
    #get all possible cases
    raw_cases = list(set(df['cases']))
    for raw_case in raw_cases:
        #clean them up:
        case = tuple(raw_case.split(','))
        #we get time coordinates the way we always do
        coords_brocken_up = action_usage(df,'cases',raw_case)
        coords = clean_coords(coords_brocken_up)
        #coords should now be a list with 1 item of formt [(start,duration)]
        if len(coords) == 1:
            coordinates[case] = coords[0]
        else:
            raise ValueError('This case seems to be used more than once: '+case)
    return coordinates


def single_value_usage(df):
    method1 = action_usage_exact(df,'Cleaned method 1','st1 \d+$')
    method2 = action_usage_exact(df,'Cleaned method 2','st1 \d+$')
    return intersect_usage(method1,method2)

REGEX_AVERAGE = 'st1 Average\s?(all)?\s?(Use)?\s?$'
REGEX_SUM = 'st1 Sum\s?(all)?\s?(Use)?\s?$'
REGEX_MEDIAN = 'st1 Median\s?(all)?\s?(Use)?\s?$'
REGEX_COUNT = 'st1 Count\s?(all)?\s?(Use)?\s?$'

def central_tendency_usage(df):
    average = merge_method_usage(df,REGEX_AVERAGE)
    sumall = merge_method_usage(df,REGEX_SUM)
    median = merge_method_usage(df,REGEX_MEDIAN)
    count = merge_method_usage(df,REGEX_COUNT)
    merging1 = merge_usage(average,sumall)
    merging2 = merge_usage(median,count)
    return merge_usage(merging1,merging2)


def regex_range(case_min,case_max):
    pattern = '^st1 {0} \- {1}\s?$'.format(case_max,case_min)
    return pattern

def range_usage(df):
    usage = []
    cases = all_cases(df)
    for case,coords in cases.items():
        start = coords[0]
        end = coords[1]
        #find min and maxes of cases for the regex
        lmin,lmax = min(case[0].split(" ")),max(case[0].split(" "))
        rmin,rmax = min(case[1].split(" ")),max(case[1].split(" "))
        
        #get all times that the range is used
        range1 = action_usage_exact(df,'Cleaned method 1',regex_range(lmin,lmax))
        range2 = action_usage_exact(df,'Cleaned method 2',regex_range(rmin,rmax))
        
        #keep only the times that fall within the current case
        range1_for_case = intersect_usage(range1,[coords])
        range2_for_case = intersect_usage(range2,[coords])
        
        # Merge when it's used on both cases
        usage.extend(clean_coords(merge_usage(range1_for_case,range2_for_case)))
    usage.sort()
    return usage

def evaluation_steps_usage(df):
    submit_usage = action_usage(df,"Selection","submit")
    evaluation_usage = action_usage(df,"Selection","evaluation")
    checkIntuition_usage = action_usage(df,"Selection","checkIntuition")
    
    ##do some merging
    merged1 = merge_usage(submit_usage,evaluation_usage)
    return merge_usage(merged1, checkIntuition_usage)

def case_usage(df):
    usage = []
    cases = all_cases(df)
    for case,coords in cases.items():
        start = coords[0]
        end = 30+20+30
        usage.append((start,end))
    return usage

def regex_count_gaps(gapvalues):
    pattern = "st\d+ Count\s?( choose\.\.\.)?(\s[({0})])+".format('|'.join(gapvalues))
    return pattern

def count_gaps_usage(df):
    usage = []
    cases = all_cases(df)
    for case,coords in cases.items():
        start = coords[0]
        end = coords[1]
        
        lcase = case[0].split(" ")
        rcase = case[1].split(" ")
        lcase.sort()
        rcase.sort()
        
        #get gap values for the regex
        gapvalues_left = set(range( int(min(lcase)) , int(max(lcase)) )) - set([int(x) for x in lcase]) 
        gapvalues_right = set(range( int(min(rcase)) , int(max(rcase)) )) - set([int(x) for x in rcase]) 

        #get all times that the range is used somewhere the method
        if len(gapvalues_left)>0:
            re_left = regex_count_gaps([str(x) for x in gapvalues_left])
            range1 = action_usage(df,'Cleaned method 1',re_left)
        else:
            range1 = action_usage(df,'Cleaned method 1',"st\d+ Count none")
            
        if len(gapvalues_right)>0:
            re_right = regex_count_gaps([str(x) for x in gapvalues_right])
            range2 = action_usage(df,'Cleaned method 2',re_right)
        else:
            range2 = action_usage(df,'Cleaned method 2',"st\d+ Count none")     

        # and keep only the times that fall within the current case
        range1_for_case = intersect_usage(range1,[coords])
        range2_for_case = intersect_usage(range2,[coords])

        # Merge when it's used on both cases
        usage.extend(clean_coords(merge_usage(range1_for_case,range2_for_case)))

    usage.sort()
    return usage


def regex_extrapolated_range(case_max1,case_min1,case_max2,case_min2):
    pattern = "(?:st\d+ {0} \- {1} st\d+ {2} \- {3}|st\d+ {2} \- {3} st\d+ {0} \- {1}) st3 Step[12] [x\+\-\\\\] Step[12]".format(case_max1,case_min1,case_max2,case_min2)
    return pattern

def extrapolated_range_usage(df):
    usage = []
    cases = all_cases(df)
    for case,coords in cases.items():
        start = coords[0]
        end = coords[1]
        
        lcase = case[0].split(" ")
        rcase = case[1].split(" ")
        lcase.sort()
        rcase.sort()
        
        #find min and maxes of cases for the regex
        lmin1,lmin2,lmax2,lmax1 = lcase[0],lcase[1],lcase[-2],lcase[-1]
        rmin1,rmin2,rmax2,rmax1 = rcase[0],rcase[1],rcase[-2],rcase[-1]
        
        #get all times that the range is used somewhere the method
        range1 = action_usage(df,'Cleaned method 1',regex_extrapolated_range(lmax1,lmin1,lmax2,lmin2))
        range2 = action_usage(df,'Cleaned method 2',regex_extrapolated_range(rmax1,rmin1,rmax2,rmin2))

#         print case, coords[0], coords[0]+coords[1]
#         print "rangel1:", regex_extrapolated_range(lmin1,lmax1)
#         print "rangel2:", regex_extrapolated_range(lmin2,lmax2)
#         print "ranger1:", regex_extrapolated_range(rmin1,rmax1)
#         print "ranger2:", regex_extrapolated_range(rmin2,rmax2)
        
        # and keep only the times that fall within the current case
        range1_for_case = intersect_usage(range1,[coords])
        range2_for_case = intersect_usage(range2,[coords])

        # Merge when it's used on both cases
        usage.extend(clean_coords(merge_usage(range1_for_case,range2_for_case)))

    usage.sort()
    return usage