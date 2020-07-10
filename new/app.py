
import argparse
import os
import logging
import pathlib
import sys
import warnings
from uszipcode import SearchEngine

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
warnings.simplefilter(action='ignore', category=Warning)

import pandas as pd
import sqlite3


class File:
    '''
    Initializes a File object that can read Farmer's Market CSV, process the file by cleaning and converting it to a database.
    '''

    def __init__(self, file):
        self.file = file
        self.clean_file = 'Processed_' + os.path.basename(self.file)
        self.dataframe = pd.read_csv(self.file)
        logging.info('File imported as dataframe: {}'.format(self.file))

        # SQL connection
        self.sql = None

    def clean(self):
        '''
        Performs data cleaning.
        '''

        self._split_season_columns()
        self._split_season_times_by_day()
        self._change_months_to_date()
        self._drop_unwanted_columns()
        self._convert_column_values_to_none()
        self._fix_noon_time()
        self._convert_month_to_date()
        self._convert_nan_to_None()


    def _split_season_columns(self):
        '''
        Splits Season dates into 2 columns, with start and end.
        '''

        change = ['Season1Date','Season2Date','Season3Date','Season4Date']
        add = ['Season1 Start Date','Season1 End Date','Season2 Start Date','Season2 End Date','Season3 Start Date','Season3 End Date','Season4 Start Date','Season4 End Date']

        x = 0
        for season in change:
            start = []
            end = []
            for index, row in self.dataframe.iterrows():
                col = row[season]
                if str(col) == "NaN":
                    start.append(None)
                    end.append(None)
                else:   
                    try:
                        test = col.split(" to ")
                        if test[1] == "":
                            test[1] = None
                        if test[0] == "":
                            test[0] = None
                        try:
                            start.append(test[0])
                        except:
                            start.append(None)
                            end.append(None)
                        try:    
                            end.append(test[1])
                        except:
                            end.append(None)    
                    except:
                        start.append(None)
                        end.append(None)
            self.dataframe[add[x]] = start
            self.dataframe[add[x + 1]] = end
            x += 2

    def _split_season_times_by_day(self):
        '''
        Splits season time by day. Creates a new columns for each day for each season.
        '''

        columns = ['Season1Time','Season2Time', 'Season3Time','Season4Time']
        days_of_week = ['Mon','Tue','Wed','Thu', 'Fri', 'Sat', 'Sun']

        #create new columns
        for season in columns:
            for day in days_of_week:
                new_column_name = season + ' ' + day
                self.dataframe[new_column_name] = None

        #parse time columns and insert into correct place 
        for season in columns:
            for index, row in self.dataframe.iterrows():
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
                                self.dataframe[season + ' ' + day][index] = time          
                except:
                    continue

    def _change_months_to_date(self):
        '''
        Replaces months with a date. Defaults to the first date of the month. Year is obtained from the last updated date.
        '''

        map_months = {
            'January': '01/01/{}',
            'February': '02/01/{}',
            'March': '03/01/{}',
            'April': '04/01/{}',
            'May': '05/01/{}',
            'June': '06/01/{}',
            'July': '07/01/{}',
            'August': '08/01/{}',
            'September': '09/01/{}',
            'October': '10/01/{}',
            'November': '11/01/{}',
            'December': '12/01/{}'
        }

        all_colms = ['Season1 Start Date', 'Season1 End Date', 'Season2 Start Date', 'Season2 End Date', 'Season3 Start Date', 'Season3 End Date', 'Season4 Start Date', 'Season4 End Date']
        for coln in all_colms:
            temp = list()
            for index, value in self.dataframe.iterrows():
                col = value[coln]
                col_update_time = value['updateTime']
                if col in map_months:
                    try:
                        temp.append(map_months.get(col).format(col_update_time.split('/')[2]))
                    except:
                        temp.append(map_months.get(col).format(col_update_time.split(' ')[2]))
                else:
                    temp.append(col)
            self.dataframe[coln] = temp

    def _drop_unwanted_columns(self, cols_to_drop = ['OtherMedia','Location','Season1Time', 'Season2Time', 'Season3Time', 'Season4Time', 'Season1Date', 'Season2Date', 'Season3Date', 'Season4Date']):
        '''
        Drops columns from the dataframe. Defaults to a pre-selected list of columns.
        '''

        for col in cols_to_drop:
            self.dataframe.drop(col, axis = 1, inplace = True)

    def _convert_column_values_to_none(self, columns = ['Organic'], replace = '-'):
        '''
        Replaces value with None for a list of columns.
        '''

        for column in columns:
            for index, value in self.dataframe.iterrows():
                col = value[column]
                if col == replace:
                    self.dataframe[column][index] = None

    def _fix_noon_time(self):
        '''
        Converts 12PM to 12 to avoid a datetime conversion failure.
        '''

        all_colms = ['updateTime','Season1 Start Date', 'Season1 End Date', 'Season2 Start Date', 'Season2 End Date', 'Season3 Start Date', 'Season3 End Date', 'Season4 Start Date', 'Season4 End Date']

        for cols in all_colms:
            for index, value in self.dataframe.iterrows():
                col = value[cols]
                try:
                    pm = col.split(' ')[2]
                    if pm == "PM":
                        test = col.split(' ')[1].split(':')[0]
                        if test == '12':
                            value_new = col.split(' ')[0] + ' ' + col.split(' ')[1]
                            self.dataframe[cols][index] = value_new
                except:
                    continue

    def _convert_month_to_date(self):
        '''
        Converts month to a date.
        '''

        months = {
            'Jan': '01',
            'Feb': '02',
            'Mar': '03',
            'Apr': '04',
            'May': '05',
            'Jun': '06',
            'Jul': '07',
            'Aug': '08',
            'Sep': '09',
            'Oct': '10',
            'Nov': '11',
            'Dec': '12'
        }

        for index, value in self.dataframe.iterrows():
            col = value['updateTime']
            col = ' '.join(col.split())
            try:
                test = col.split(' ')
                if test[0] in months:
                    string = months[test[0]] + '/' + test[1] + '/' + test[2] + ' ' + test[3]
                    self.dataframe['updateTime'][index] = string
            except:
                continue

    def _convert_nan_to_None(self):
        '''
        Replaces all NaN values to None.
        '''

        self.dataframe = self.dataframe.where(pd.notnull(self.dataframe), None)


    def save_as_csv(self):
        '''
        Saves the cleaned dataframe as a CSV. Processed tag is appended to the original file name and saved in the current directory.
        '''

        if os.path.exists(self.clean_file):
            os.remove(self.clean_file)
        self.dataframe.to_csv(self.clean_file)
        logging.info('Processed file saved as: {}'.format(self.clean_file))

    def convert_to_database(self, table = 'markets'):
        '''
        Converts a cleaned dataframe to a SQL table named markets.
        '''

        self.dataframe.columns = self.dataframe.columns.str.strip()
        if os.path.exists('{}.db'.format(table)):
            os.remove('{}.db'.format(table))
        self.sql = sqlite3.connect('{}.db'.format(table))
        self.dataframe.to_sql(table, self.sql)
        self.sql.close()

        logging.info('Database exported as: {}.db'.format(table))

    def _add_missing_zip_codes(self):
        '''
        Uses coordinates to add missing zipcodes.
        '''

        search = SearchEngine(simple_zipcode = True)
        for index, value in self.dataframe.iterrows():
            zipcode = value['zip']
            x = value['x']
            y = value['y']
            if zipcode == None:
                try:
                    result = search.by_coordinates(y, x, radius=30, returns=1)
                    self.dataframe['zip'][index] = result[0].zipcode
                except:
                    pass


    def _add_missing_locations_using_zip(self):
        '''
        Replaces all missing locations with a valid city, county and zip.
        '''

        us_state_abbrev = {
            'Alabama': 'AL',
            'Alaska': 'AK',
            'American Samoa': 'AS',
            'Arizona': 'AZ',
            'Arkansas': 'AR',
            'California': 'CA',
            'Colorado': 'CO',
            'Connecticut': 'CT',
            'Delaware': 'DE',
            'District of Columbia': 'DC',
            'Florida': 'FL',
            'Georgia': 'GA',
            'Guam': 'GU',
            'Hawaii': 'HI',
            'Idaho': 'ID',
            'Illinois': 'IL',
            'Indiana': 'IN',
            'Iowa': 'IA',
            'Kansas': 'KS',
            'Kentucky': 'KY',
            'Louisiana': 'LA',
            'Maine': 'ME',
            'Maryland': 'MD',
            'Massachusetts': 'MA',
            'Michigan': 'MI',
            'Minnesota': 'MN',
            'Mississippi': 'MS',
            'Missouri': 'MO',
            'Montana': 'MT',
            'Nebraska': 'NE',
            'Nevada': 'NV',
            'New Hampshire': 'NH',
            'New Jersey': 'NJ',
            'New Mexico': 'NM',
            'New York': 'NY',
            'North Carolina': 'NC',
            'North Dakota': 'ND',
            'Northern Mariana Islands':'MP',
            'Ohio': 'OH',
            'Oklahoma': 'OK',
            'Oregon': 'OR',
            'Pennsylvania': 'PA',
            'Puerto Rico': 'PR',
            'Rhode Island': 'RI',
            'South Carolina': 'SC',
            'South Dakota': 'SD',
            'Tennessee': 'TN',
            'Texas': 'TX',
            'Utah': 'UT',
            'Vermont': 'VT',
            'Virgin Islands': 'VI',
            'Virginia': 'VA',
            'Washington': 'WA',
            'West Virginia': 'WV',
            'Wisconsin': 'WI',
            'Wyoming': 'WY'
        }

        abbrev_us_state = dict(map(reversed, us_state_abbrev.items()))
        search = SearchEngine(simple_zipcode = True)

        for index, value in self.dataframe.iterrows():
            try:
                zipcode = str(value['zip'])
                city = value['city']
                county = value['County']
                state = value['State']
                zipcode_dict = search.by_zipcode(zipcode)
                zipcode_dict = zipcode_dict.to_dict()
                if city == None:
                    new_city = zipcode_dict["major_city"]
                    self.dataframe['city'][index] = new_city 
                if county == None:
                    new_county = zipcode_dict["county"]
                    self.dataframe['County'][index] = new_county
                if state == None:
                    new_state = zipcode_dict["state"]
                    new_state = abbrev_us_state[new_state]
                    self.dataframe['State'][index] = new_state
            except:
                pass
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Data cleanining and database converter for USDA Farmers Market data')
    group = parser.add_mutually_exclusive_group(required = True)
    group.add_argument('--file', '-f', type=str, help='Absolute path to CSV containing data')
    group.add_argument('--database', '-db', type=str, help='Absolute path to database file to perform queries')
    parser.add_argument('--clean', required=False, action='store_true', default=False, help='Performs data cleaning')
    parser.add_argument('--to-database', required=False, action='store_true', default=False, help='Converts a cleaned source CSV to a database')
    parser.add_argument('--apply-ic', required=False, action='store_true', default=False, help='Apply integrity constrains on the database')
    parser.add_argument('--query', '-q', required=False, action='store_true', default=False, help='Perform queries when a database file is passed to the program.')

    args = parser.parse_args()

    if args.file:

        if not os.path.exists(args.file):
            logging.error('No file found at path: {}'.format(args.file))
            sys.exit(1)

        if pathlib.Path(args.file).suffix not in ('.csv', '.db'):
            logging.error('Input file is not a CSV/DB: {}'.format(args.file))
            sys.exit(1)

        file = File(args.file)

        if args.clean:
            file.clean()
            file.save_as_csv()

        if args.to_database:
            file.convert_to_database()

