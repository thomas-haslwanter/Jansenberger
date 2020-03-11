"""
sqlite-Database for Jansenberger


"""
# author: Thomas Haslwanter
# date:   Feb-2020

# Import required packages
import sqlite3
import pandas as pd
import os
import yaml

def generate(db_name):
    """Generate a new data-base
    
    Parameters
    ----------
        db_name : str
                Name of the database
            
    Return
    ------
        None
        
    Notes
    -----
        The generated sample database has the following tables, with the corresponding fields:

        Language:   id / token / english / german
        Settings: id / variable / value 
        Subjects: id / first_name / last_name / dob / sv_nr / faller / comments
        Experimentor: id / first_name / last_name / comments
        Paradigms: id / abbreviation / description 
        Recordings: id / id_subject / id_experimentor / id_paradigm / date_time / filename / comments / quality / num_sensors
        
    """
    # Create the database
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    # Create the "Language"-table
    language_sql = """
        CREATE TABLE Language (
        id integer PRIMARY KEY,
        token text NOT NULL,
        english text NOT NULL,
        german text NOT NULL)"""
    cur.execute(language_sql)

    # Create the "Settings"-table
    settings_sql = """
        CREATE TABLE Settings (
        id integer PRIMARY KEY,
        variable text NOT NULL,
        value text NOT NULL)"""
    cur.execute(settings_sql)

    # Create the "Subjects"-table
    subjects_sql = """
        CREATE TABLE Subjects (
        id integer PRIMARY KEY,
        first_name text NOT NULL,
        last_name text NOT NULL,
        dob text NOT NULL,
        sv_nr integer NOT NULL,
        faller integer NOT NULL,
        comments text NOT NULL)"""
    cur.execute(subjects_sql)

    # Create the "Experimentors"-table
    experimentor_sql = """
        CREATE TABLE Experimentors (
        id integer PRIMARY KEY,
        first_name text NOT NULL,
        last_name text NOT NULL,
        comments text NOT NULL)"""
    cur.execute(experimentor_sql)

    # Create the "Paradigms"-table
    paradigms_sql = """
        CREATE TABLE Paradigms (
        id integer PRIMARY KEY,
        abbreviation text NOT NULL,
        description text NOT NULL)"""
    cur.execute(paradigms_sql)

    # Recordings: id / id.Subjects / id.Subjects.experimentor / id.Paradigm / date_time / filename / comments
    # Create the "Recordings"-table
    recordings_sql = """
        CREATE TABLE Recordings (
        id integer PRIMARY KEY,
        id_subject integer NOT NULL,
        id_experimentor integer NOT NULL,
        id_paradigm integer NOT NULL,
        date_time text NOT NULL,
        filename text NOT NULL,
        num_sensors integer NOT NULL,
        quality integer NOT NULL,
        comments text )"""
    cur.execute(recordings_sql)

    conn.commit()
    conn.close()
    return 


def fill(db_name):
    """Fill the data-base
    
    Parameters
    ----------
        db_name : str
                Name of the database
            
    Return
    ------
        None
        
    Notes
    -----
        The generated sample database has the following tables, with the corresponding fields:

        Language:   id / token / english / german
        Settings: id / variable / value 
        Subjects: id / first_name / last_name / dob / sv_nr / faller / comments
        Experimentor: id / first_name / last_name / comments
        Paradigms: id / abbreviation / description 
        Recordings: id / id_subject / id_experimentor / id_paradigm / date_time / filename / num_sensors / comments
        
    """
    
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
    # Language
    with open('lang_en.yaml', 'r') as fh_en:
        lang_en = yaml.load(fh_en, Loader=yaml.FullLoader)
    with open('lang_de.yaml', 'r') as fh_de:
        lang_de = yaml.load(fh_de, Loader=yaml.FullLoader)
        
    lang_sql = 'INSERT INTO Language (id, token, english, german) VALUES (?,?,?,?)'
    for num, key in enumerate(lang_en):
        cur.execute(lang_sql, (num, key, lang_en[key], lang_de[key]))
    
    # Settings
    settings_sql = 'INSERT INTO Settings (id, variable, value) VALUES (?,?,?)'
    with open('settings.yaml', 'r') as fh:
        defaults = yaml.load(fh, Loader=yaml.FullLoader)
    for num, key in enumerate(defaults):
        cur.execute(settings_sql, (num, key, defaults[key]))

    # Subjects
    # Subjects: id / first_name / last_name / dob / sv_nr / experimentor / faller / comments
    subject_sql = 'INSERT INTO Subjects (id, first_name, last_name, dob, sv_nr, faller, comments) VALUES (?,?,?,?,?,?,?)'
    df_subjects = pd.read_csv('subjects.txt', skipinitialspace=True, header=None)
    for index, subject in df_subjects.iterrows():
        cur.execute(subject_sql, (index, subject[1], subject[0], '2000-01-01', 0, 0, 'funny') )

    # Experimentors
    # Experimentors: id / first_name / last_name / comments
    experimentor_sql = 'INSERT INTO Experimentors (id, first_name, last_name, comments) VALUES (?,?,?,?)'
    df_experimentors = pd.read_csv('experimentors.txt', skipinitialspace=True, header=None)
    for index, experimentor in df_experimentors.iterrows():
        cur.execute(experimentor_sql, (index, experimentor[1], experimentor[0], 'not so funny') )

    # Paradigms
    # Paradigms: id / abbreviation / description 
    paradigm_sql = 'INSERT INTO Paradigms (id, abbreviation, description) VALUES (?,?,?)'
    df_paradigms = pd.read_csv('paradigms.txt', skiprows=2, skipinitialspace=True)
    for index, paradigm in df_paradigms.iterrows():
        cur.execute(paradigm_sql, (index, paradigm.Abbreviation, paradigm.Full_Name))

    # Recordings
    # Recordings: id / id_subject / id_experimentor / id_paradigm / date_time / filename / comments
    recordings_sql = 'INSERT INTO Recordings (id, id_subject, id_experimentor, id_paradigm, date_time, filename, comments, num_sensors, quality) VALUES (?,?,?,?,?,?,?,?,?)'
    df_experiments = pd.read_csv('experiments_list.txt', skipinitialspace=True, header=None)
    for index, experiment in df_experiments.iterrows():
        cur.execute(recordings_sql,
                (index, experiment[0], experiment[1], experiment[2],
                    experiment[3], experiment[4], experiment[5], experiment[6], 2) )

        
    conn.commit()
    conn.close()
    return 


def query(db_name):
    """
    Sample query of a database with linked tables
    
    Parameters
    ----------
        db_name : str
                Name of the database
                
    Return
    ------
        None
    """

    # Connect to an existing database
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
    # Now that the data are entered, an example of how to extract them
    query_sql = """
        SELECT Subjects.first_name, Subject.last_name, paradigm.abbreviation,
            exercise.date, exercise.start, exercise.stop,
            trial.start_time
        FROM subjects subject
        INNER JOIN exercises exercise
        ON subject.id=exercise.user_id
        INNER JOIN paradigms paradigm
        ON paradigm.id = exercise.paradigm_id
        INNER JOIN trials trial
        ON exercise.id = trial.exercise_id
        """
    df = pd.read_sql_query(query_sql, conn)
    print(df)

    conn.close()
    
    
def create_view(db_name):
    """
    Sample view of a database with linked tables
    
    Parameters
    ----------
        db_name : str
                Name of the database
                
    Return
    ------
        None
    """

    # Connect to an existing database
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
    # Now that the data are entered, an example of how to extract them
    view_sql = """
        CREATE VIEW v_exercises
        AS
        SELECT Subjects.first_name, Subjects.last_name, Subjects.id, abbreviation,
            date_time, filename, Experimentors.first_name,
            Experimentors.last_name, Recordings.comments, quality, num_sensors
        FROM Recordings
        INNER JOIN Subjects
        ON Subjects.id = Recordings.id_subject
        INNER JOIN Paradigms 
        ON Paradigms.id = Recordings.id_paradigm
        INNER JOIN Experimentors
        ON Experimentors.id = Recordings.id_experimentor
        """
    conn.execute(view_sql)
    conn.commit()
    conn.close()
    

def query_TableView(db_name, table):
    """
    query a full table
    
    Parameters
    ----------
        db_name : str
                Name of the database
        table : str
                Name of the table
                
    Return
    ------
        df_table : pandas DataFrame
                Table
    """

    # Connect to an existing database
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    
    # Now that the data are entered, an example of how to extract them
    query_sql = f'SELECT * FROM {table}'
    df = pd.read_sql_query(query_sql, conn)
    conn.close()

    # print(df)
    return df


def export_view(db_name, xls_name, view='v_exercises'):
    """
    Export a view to an MS-Excel file

    Parameters
    ----------
    db_name : string
            Name of the sqlite database
    xls_name : string
            Name of the output-file (MS-Excel format)
    view : string
        Database-view for the export

    """

    df = query_TableView(db_name, view)
    df.to_excel(xls_name)

if __name__ == '__main__':
    
    """
    # Set the parameters
    in_file = 'test_data.txt'
    db_name = 'test.db'
    
    # Just for debugging, remove any existing file with that name
    if os.path.exists(db_name):
        os.remove(db_name)
        
    generate(db_name)
    fill(db_name)
    #query_db(db_name)
    query_TableView(db_name, 'Subjects')
    create_view(db_name)
    query_TableView(db_name, 'v_exercises')
    input('Done')
    """ 
    
    db_name = 'Jansenberger.db'
    xls_name = 'out.xlsx'

    df = export_view(db_name, xls_name)
    print(f'The database has been exported to {xls_name}.')
