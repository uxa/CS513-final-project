import pandas as pd

df = pd.read_csv('Farmers-Market-OR.csv')

columns = ['Season1Time','Season2Time', 'Season3Time','Season4Time']
days_of_week = ['Mon','Tue','Wed','Thu', 'Fri', 'Sat', 'Sun']

#create new columns
for season in columns:
    for day in days_of_week:
        new_column_name = season + ' ' + day
        df[new_column_name] = None

#parse time columns and insert into correct place 
for season in columns:
    for index, row in df.iterrows():
        try:
            time_all = row[season]
            time_list = time_all.split(";")
            del time_list[-1]
            for item in time_list:
                day = item.split(':',1)[0]
                time = item.split(':',1)[1]
                time = time.strip()
                #print(day,time)
                for x in days_of_week:
                    if x == day:
                        text = season + ' ' + day
                        df[season + ' ' + day][index] = time          
        except:
            continue
df.to_csv('Farmers-Market-OR-Pandas.csv') 