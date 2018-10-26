from utils import *
import matplotlib.pyplot as plt
import seaborn as sns

colors = {"Cases":"white",
         "Now try working on this new example":"#252525",
         "intuition": "#969696",
         "Single value": "red",
         'Central tendency': "#33a02c",
         'Other distance': "#6a3d9a",
#          'Average': "#6a3d9a",
#          'Sum': "#1f78b4",
          'Count gaps': "red",
          'Range': "#1f78b4",
         'Count all': "#ff7f00",
         'Other': "yellow", 
         'evaluation steps': "#525252",
          'submit': "#525252",
          "Build":'black',
          "delete":'black',
          "deleteAll":'black',
        }
column_to_use = {"Now try working on this new example":"Feedback Text",
                 "intuition": "Selection",
                 "submit": "Selection",
                 "evaluation": "Selection",
                 "checkIntuition": "Selection",
                 "delete":"Selection",
                 "deleteAll":"Selection",
                }

function_to_use = {"Cases":case_usage,
                   "Single value":single_value_usage,
                   "Central tendency":central_tendency_usage,
                   "Range":range_usage,
                   "Other distance":distance_usage,
                   "Count gaps":count_gaps_usage,
                   "Build": build_events,
                   "evaluation steps":evaluation_steps_usage,
                   'Count all': count_all_usage,
                   "Other":other_usage}

to_plot = ["Cases","intuition",'Single value','Central tendency',"Count all","Count gaps",'Range',"Other distance","Other","Build","delete","deleteAll","submit","evaluation steps"]

def plot(df,to_plot,colors, column_to_use, function_to_use):
    fig = plt.figure(figsize=(18,9))
    ax = plt.subplot()
    spacing =10
    pos = 0
    max_time = 0
    actions = list(reversed(to_plot))
    black = '#252525'
    for i,action in enumerate(actions):
        if action == "Cases":
            cases = all_cases(df)
            for case,coords in all_cases(df).items():
                left = [float(x) for x in case[0].split(" ")]
                right = [float(x) for x in case[1].split(" ")]
                ymax = max(max(left),max(right))
                ymin = min(min(left),min(right))
                Xl = [coords[0]+30]*len(left)
                Yl = [(l-ymin+1)/(ymax-ymin+1)*(spacing-2.5)+1+pos for l in left]
                Xr = [coords[0]+30+20]*len(right)
                Yr = [(r-ymin+1)/(ymax-ymin+1)*(spacing-2.5)+1+pos for r in right]
                ax.plot(Xl,Yl,'.',color="darkgrey",markersize=10)
                ax.plot(Xr,Yr,'.',color="darkgrey",markersize=10)
                case_pos = pos
        if action in column_to_use.keys():
            action_use = action_usage(df,column_to_use[action],action)
        else:
            action_use = function_to_use[action](df)
        if action_use:
            max_time = max(max_time,sum(action_use[-1]))
            ax.broken_barh(action_use,(pos,spacing),facecolors=colors[action],alpha=1,linewidth=0)
        pos += spacing

    coords = zip(df[df['Feedback Text'].str.contains("Good. Click Done to continue.",na=False)]['Time_seconds'],df[df['Feedback Text'].str.contains("Good. Click Done to continue.",na=False)]['Duration'])
    solutions_left = df[df['Feedback Text'].str.contains("Good. Click Done to continue.",na=False)]['Cleaned method 1']
    solutions_right = df[df['Feedback Text'].str.contains("Good. Click Done to continue.",na=False)]['Cleaned method 2']
    solutions = [sl+' | '+sr for sl,sr in zip (solutions_left,solutions_right)]

    for s,coord in zip (solutions,coords):
        ax.text(coord[0]-5,case_pos+spacing/2,s,horizontalalignment='right',fontsize=14)

#     #Add horizontal bar
#     ax.broken_barh([(0,ax.get_xlim()[1])],((len(actions))*spacing,spacing),facecolors='white',alpha=1,linewidth=0)

    #Add new case bar
    new_case = "Now try working on this new example"
    action_use = action_usage(df,column_to_use[new_case],new_case)
    case_use = [(x-10,10) for (x,y) in action_use]+[(-10,10)]
    if action_use:
        max_time = max(max_time,sum(action_use[-1]))
        ax.broken_barh(case_use,(0,(len(actions))*spacing),facecolors="white",alpha=1,linewidth=0)

    #Add labels
    ax.set_xlabel('minutes in activity',fontsize=13)
    ax.set_xticks(range(0,int(max_time),60))
    ax.set_xticklabels([str(x/60)+''if x in range(0,int(max_time),60*5) else "" for x in range(0,int(max_time),60)],fontsize=13)
    ax.set_yticks(range(spacing/2,len(actions)*spacing,spacing))
    ax.set_yticklabels([a.capitalize() for a in actions],fontsize=15)
    ax.grid(True)
    plt.show()