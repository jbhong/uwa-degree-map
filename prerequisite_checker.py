"""
    program to check the prerequisite tree for UWA units and degrees
    Written by : Jin Hong
    date       : 15 March 2023
"""

import requests
from bs4 import BeautifulSoup
import pickle
import pathlib
import re
from itertools import product
import sys

UNIT_PATH = "./units/"
COURSE_PATH = "./courses/"

class Unit:
    URL = "https://handbooks.uwa.edu.au/unitdetails?code="
    PREREQ = "./prereq_list.txt"
    
    def __init__(self, ucode="", text=[], get_text=True) -> None:
        self.code = ucode
        if get_text:
            text = self.get_text()
            if text == []:
                print("There was no text data provided, check your url...")
                return
        self.text = text
        self.title = text[text.index("UWA Handbook 2023") + 1]

        self.description = ""
        i = text.index("Description") + 1
        j = [text.index(j) for j in text if j.startswith("Credit")][0]
        for k in range(i, j):
            self.description += text[k].strip() + "\n"
        
        self.credit = int(text[j].strip("Credit").strip("points").strip())
        
        self.offering = "NA"
        i = [text.index(j) for j in text if j.startswith("Offering")][0]
        j = text.index("Outcomes")
        for k in range(i, j):
            self.offering += text[k]
        rows = self.offering.split("Semester")

        self.offer = []
        self.semester = set()
        for row in rows:
            if "1" in row:
                self.semester.add(1)
                if "Face" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Face to face"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Face to face"))
                elif "Restricted" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Online Restricted"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Online Restricted"))
                elif "Online timetabled" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Online timetabled"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Online timetabled"))
                    else:
                        self.offer.append(("Semester 1", "Online", "Online timetabled"))
                elif "Online" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 1", "UWA (Perth)", "Online"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 1", "Albany", "Online"))
            elif "2" in row:
                self.semester.add(2)
                if "Face" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Face to face"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Face to face"))
                elif "Restricted" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Online Restricted"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Online Restricted"))
                elif "Online timetabled" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Online timetabled"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Online timetabled"))
                    else:
                        self.offer.append(("Semester 2", "Online", "Online timetabled"))
                elif "Online" in row:
                    if "UWA (Perth)" in row:
                        self.offer.append(("Semester 2", "UWA (Perth)", "Online"))
                    elif "Albany" in row:
                        self.offer.append(("Semester 2", "Albany", "Online"))
            elif "Not available" in row:
                self.offer = "Not available"

        self.ugdetails = "Check the handbook"
        i = [text.index(j) for j in text if j.startswith("Offering")][0]
        j = text.index("Outcomes")
        while not text[i].startswith("Details for undergraduate") and i < j:
            i += 1
        if text[i].startswith("Details for undergraduate"):
            text[i] = text[i].replace("Details for undergraduate courses", "")

            self.ugdetails = ""
            for k in range(i, j):
                self.ugdetails += text[k].replace("Level ", " Level ").strip() + "\n"
        self.ugdetails = self.ugdetails.strip()

        self.outcomes = ""
        i = text.index("Outcomes") + 1
        j = [text.index(j) for j in text if j.startswith("Assessment")][0]
        for k in range(i, j):
            self.outcomes += text[k] + "\n"

        try:
            self.coordinator = text[text.index("Unit Coordinator(s)") + 1]
        except:
            print(f"No coordinator in this unit: {self.code}")
            self.coordinator = ""
        try:
            prereq = text[text.index("Prerequisites") + 1].split("or ")
            prereq = " or ".join([row.strip() for row in prereq]).split("and ")
            prereq = " and ".join([row.strip() for row in prereq])
            prereq = prereq.replace("Enrolment in", "Enrolment in ")
            prereq = prereq.replace("FoundationsandCITS1401", "Foundations and CITS1401")
            prereq = prereq.replace("Java andM", "Java and M")
            prereq = prereq.replace("Bachel or", "Bachelor")
            prereq = prereq.replace(" in   in the", " in the ")
            prereq = prereq.replace("specialisationorthe", "specialisation or the")
            prereq = prereq.replace("IntelligenceorBachelor", "Intelligence or Bachelor")
            prereq = prereq.replace("in in", "in")
            prereq = prereq.replace("the the", "the")
            prereq = prereq.replace(" inthe ", " in the ")
            prereq = prereq.replace("Scienceorthe", "Science or the")
            prereq = prereq.replace(" maj or ", " major")
            prereq = prereq.replace("majorand", "major and")
            prereq = prereq.replace("pri or", "prior")
            prereq = prereq.replace(" including", " including ")
            prereq = prereq.replace("of96", "of 96")
            prereq = prereq.replace("  ", " ")
            if " f or " in prereq:
                prereq = prereq.replace(" f or ", " for ")
            self.prereq = prereq
        except:
            print(f"No prerequisites in this unit: {self.code}")
            self.prereq = ""
        
        self.prereqlist = []
        self.update_prereqlist()


        try:
            incomp = text[text.index("Incompatibility") + 1].split("or ")
            incomp = " or ".join([row.strip() for row in incomp]).split("and ")
            incomp = " and ".join([row.strip() for row in incomp])
            if " f or " in incomp:
                incomp = incomp.replace(" f or ", " for ")
            incomp = incomp.replace("Enrolment in", "Enrolment in ")
            incomp = incomp.replace("FoundationsandCITS1401", "Foundations and CITS1401")
            self.incompatibility = incomp
        except:
            print(f"No incompatibility in this unit: {self.code}")
            self.incompatibility = ""

    def __str__(self):
        offer = f"\n{'':22}".join([f"{i} | {j:12} | {k}" for (i, j, k) in self.offer])
        return (f"{'Unit Code':20}: {self.code}\n"
                f"{'Unit Title':20}: {self.title}\n"
                f"{'Unit Credit':20}: {self.credit}\n"
                f"{'Unit Offering':20}: {offer}\n"
                f"{'Unit Semesters':20}: {sorted(self.semester)}\n"
                f"{'Unit UG details':20}: {self.ugdetails}\n"
                f"{'Unit Coordinator':20}: {self.coordinator}\n"
                f"{'Unit Prerequisites':20}: {self.prereq}\n"
                f"{'Unit Incompatibility':20}: {self.incompatibility}\n"
                f"\n"
                f"{'Unit Description':20}: {self.description}\n"
                f"{'Unit Outcomes':20}: {self.outcomes}"
                #f"{self.offering}"
                )


    def update_values(self):
        """call all the update functions when saving unit"""
        self.update_prereqlist()

    def update_prereqlist(self) -> None:
        """update the prereq list in case modified"""
        # do some prep work
        if "Data Structures and Algorithms" in self.prereq:
            self.prereq = self.prereq.replace("Data Structures and Algorithms",
                                "Data Structures & Algorithms")
        if "Theory and Methods" in self.prereq:
            self.prereq = self.prereq.replace("Theory and Methods",
                                "Theory & Methods")
        if "Analysis and Visualisation" in self.prereq:
            self.prereq = self.prereq.replace("Analysis and Visualisation",
                                "Analysis & Visualisation")
        if "Intelligence and Adaptive" in self.prereq:
            self.prereq = self.prereq.replace("Intelligence and Adaptive",
                                "Intelligence & Adaptive")  
        if "Mobile and Wireless" in self.prereq:
            self.prereq = self.prereq.replace("Mobile and Wireless",
                                "Mobile & Wireless")  
        if "Tools and Scripting" in self.prereq:
             self.prereq = self.prereq.replace("Tools and Scripting",
                                "Tools & Scripting")  
        if "Testing and Quality" in self.prereq:
             self.prereq = self.prereq.replace("Testing and Quality",
                                "Testing & Quality")  
        if "6 points of programming" in self.prereq:
            self.prereq = self.prereq.replace("6 points of programming",
                                "CITS1401 or CITX1401")
        elif "12 points of programming" in self.prereq:
            self.prereq = self.prereq.replace("12 points of programming",
                                "CITS2002 or CITS2005")

        #list of all unit codes in prereq and "or" and "and"
        matches = "".join(self.match_code(self.prereq)).strip("andor ")
        #print("MATCHES", matches)
        and_groups = [code for code in matches.split(' and ') if code.strip("andor ")]
        # Split each 'and' group by 'or' separator
        or_groups = [[code for code in group.split(' or ') if code.strip("andor ")] 
                     for group in and_groups]

        # Generate all possible combinations of subjects
        self.prereqlist = [list(pair) for pair in list(product(*or_groups)) if pair]        

    def match_code(self, text):
        pattern = r'\b[a-zA-Z]{4}\d{4}\b|\b and \b|\b or \b'
        matches = re.findall(pattern, text)
        return matches  

    def save(self, fname=""):
        """saves the unit file"""
        self.update_values()
        fname = self.code if fname == "" else fname
        with open(UNIT_PATH + fname, 'wb') as f:
            pickle.dump(self, f)
    

    def load(self, code):
        """returns the saved unit file"""
        try:
            with open(UNIT_PATH + code, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"UnitClassError: file [{code}] doesn't exist... I'll get it from the handbook and make it...")
            try:
                self.code = code
                text = self.get_text()
                unit = Unit(code, text, False)
                unit.save()
                return unit
            except:
                print(f"Could not create unit: {code}")


    def update(self):
        """updates the content with a fresh pull from the handbook"""
        try:
            text = self.get_text()
            unit = Unit(self.code, text, False)
            unit.save()
            return unit
        except:
            print(f"Could not create unit: {self.code}")
    
    def delete(self):
        """checks the handbook online and deletes the unit file if not in the handbook"""
        if requests.get(Unit.URL + self.code).status_code != 200:
            pathlib.Path(UNIT_PATH + self.code).unlink()

    def get_text(self):
        """returns the text from the web"""
        if len(self.code) > 0:
            response = requests.get(Unit.URL + self.code)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                return [s.strip() for s in soup.get_text().splitlines() if s.strip()]
            else:
                print(f"the url for unit, {self.code}, doesn't exist... try again...")
        return []


class UnitList:
    URL = 'https://handbooks.uwa.edu.au/unitdetails?code='

    def __init__(self, fname="", ulist=[]) -> None:
        self.fname = fname
        self.ulist = ulist
        self.units = self.get_unit_list() #this is a dictionary of code:Unit
        
    def __contains__(self, code):
        return code in self.units.keys()

    def __str__(self):
        out = ""
        for unit in list(self.units.keys()):
            out += f"{unit}, "
        return out.strip(", ")


    def get_unit_list_helper(self, codes):
        """get units helper"""
        units = {}
        for code in codes:
            try:
                unit = Unit().load(code)
            except FileNotFoundError:
                print(f"the unit, {code}, doesn't exist, so making it...")
                unit = Unit(code)
            except:
                print(f"could not make the unit, {code}... skipping...")
                continue
            units[code] = unit
        return units


    def get_unit_list(self):
        """returns the list of unit code"""
        if len(self.fname) > 0:
            try:
                with open(self.fname) as f:
                    codes = [code.strip() for code in f.readlines()]
                    return self.get_unit_list_helper(codes)
            except:
                print(f"the unit list: {self.fname}, doesn't exist... try making it...")
        elif len(self.ulist) > 0:
            return self.get_unit_list_helper(self.ulist)
        return {}


    def update_unit_list(self, unit) -> None:
        """updates the unit list if missing"""
        if unit not in self.units:
            self.units[unit.code] = unit
            with open(self.fname, 'w') as f:
                for code in sorted(list(self.units.keys())):
                    f.write(code + "\n")

    def set_fname(self, fname):
        """set fname"""
        self.fname = fname

    def save(self, fname=""):
        """save the current list of units to file fname"""
        fname = self.fname if len(fname) == 0 else fname
        output = "*" * 30
        output += "\n"
        for _, unit in sorted(self.units.items()):
            output += str(unit)
            output += "\n"
            output += "*" * 30
            output += "\n"
            
        with open(fname, "w") as f:
            f.write(output)

    def remove_none_units(self) -> None:
        """go through the unit list and remove if not found in the handbook online"""
        codes = set([code for code in self.units
                        if requests.get(UnitList.URL + code).status_code != 200])
        for code in codes:
            del(self.units[code])
            pathlib.Path(UNIT_PATH + code).unlink()

        with open(self.fname, 'w') as f:
            for code in sorted(list(self.units)):
                f.write(code + "\n")


    def get_next_unit_code(self, ucode, bound=90, start='A') -> str:
        """ ucode is the unit code, which is always 4 letters and 4 digits
            A-Z ord is 65 to 90.
            0-0 ord is 48 to 57.
            Call with bound 90 and start 'A' for letter code
            Call with bound 57 and start '0' for number code
        """
        ucode = list(ucode)
        char_ind = 3          #start with the last letter
        
        #past Z so increment the next letter
        while char_ind >= 0:
            if ord(ucode[char_ind]) + 1 > bound:
                ucode[char_ind] = start 
            else:
                ucode[char_ind] = chr(ord(ucode[char_ind]) + 1)
                char_ind = 0
            char_ind -= 1

        return ''.join(ucode)       

    def is_code(self, ucode):
        """check if ucode is actually code"""
        return (len(ucode) == 8 and 
                ucode[4:].isnumeric() and
                ucode[:4].isalpha())


    def find_units(self, ucode="", stop="6000") -> list:
        """ Try entire possible unit codes and retrieve all units.
            This is to discover any new units.
            if ucode is provided, only that code will be checked.
            This is VERY slow.
        """
        #some starting unit code
        if ucode == "":
            uletter = "AAAA" 
            unumber = "1000"
        elif self.is_code(ucode):
            uletter = ucode[:4]
            unumber = ucode[4:]
        else:
            print(f"the code, {ucode}, is not valid unit code... exiting...")
            return
 
        while (uletter + unumber != "ZZZZ" + stop):
            print(f"Checking: {uletter + unumber}")
            if (uletter + unumber) not in self.units:
                unit = Unit(uletter + unumber)
                if len(unit.text) > 0:
                    print(f"Found unit: {unit.code}!")

                    #update the unit list
                    self.update_unit_list(unit)

                    #save the new unit object
                    unit.save()
            else:
                print(f"{uletter + unumber} already in the list... skipping...")
            if unumber < stop:
                unumber = self.get_next_unit_code(unumber, 57, "0")
            elif (unumber == stop):
                uletter = self.get_next_unit_code(uletter, 90, "A")
                unumber = "1000"
                if (len(ucode) > 0): #finished for the given unit code
                    return
        return



    def save_unit(self, unit):
        """saves the unit object"""
        with open(UNIT_PATH + unit.code, 'wb') as f:
            pickle.dump(unit, f)


class Course:
    def __init__(self, url=None) -> None:
        self.url = url
        self.text = self.get_text()
        self.title = ""
        self.conversion = {}
        self.bridging = {}
        self.core = {}
        self.option = {}
        self.unitlist = UnitList()
        if url and len(self.text) > 0:
            self.title = self.text[0].split(":")[0].strip()
            self.conversion, self.core, self.option = self.find_units()
            units = []
            [units.extend(value) for value in self.conversion.values()]
            [units.extend(value) for value in self.core.values()]
            [units.extend(value) for value in self.option.values()]
            self.unitlist = UnitList(ulist=units)
                    
    def __str__(self):
        result = ""
        for level in range(0, 6):
            if level in self.conversion:
                result += f"Conversion units:\n"
                for unit in self.conversion[level]:
                    result += f"{unit}\n"
            if level in self.bridging:
                result += f"Bridging units:\n"
                for unit in self.bridging[level]:
                    result += f"{unit}\n"
            if level in self.core:
                result += f"Level {level} Core:\n"
                for unit in self.core[level]:
                    result += f"{unit}\n"
            if level in self.option:
                result += "\n"
                for unit in self.option[level]:
                    result += f"{unit}\n"
            result += "\n"
        return result.strip() 

    def get_text(self):
        """fetch the text data from the url"""
        response = requests.get(self.url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return [s.strip() for s in soup.get_text().splitlines() if s.strip()]
        else:
            print("the url for the course doesn't exist...")
        return []
    
    def save(self, fname=""):
        """save the current object into a file"""
        fname = self.title if len(fname) == 0 else fname
        with open(COURSE_PATH + fname, 'wb') as f:
            pickle.dump(self, f)

    def load(self, fname):
        """returns the saved course file"""
        try:
            with open(COURSE_PATH + fname, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            print(f"this course: {fname}, doesn't exist... try making it...")
        return None
    
    def update(self):
        """update units in the course from handbook"""
        for code, unit in self.unitlist.units.items():
            if not type(unit):
                self.unitlist.units[code] = unit.update()
            

    def add_code(self, text, index, codes):
        """check if the specified row starts with unit code"""
        if (len(text[index].split()[0]) == 8 and 
                text[index].split()[0][4:].isnumeric() and
                ("(0)" not in text[index].split())):
            codes.append(text[index].split()[0])
        return codes
    

    def get_units(self, core, option, conversion, level, text):
        """ get units from the course list
            it doesn't keep track of 0 point units.
            still work needs done for MPE.
        """
        #do the conversion stuff
        index = 0
        codes = []
        while (index < len(text) and 
                (not text[index].startswith("Core")) and 
                (not text[index].startswith("Option")) and 
                (not text[index].startswith("Level"))):
            codes = self.add_code(text, index)
            index += 1
        if len(codes) > 0:
            conversion[0] = codes
        index += 1

        #do the core stuff
        codes = []
        while (index < len(text) and 
                (not text[index].startswith("Option")) and 
                (not text[index].startswith("Level"))):
            codes = self.add_code(text, index)
            index += 1
        if len(codes) > 0:
            core[level] = codes
        
        #do the option stuff
        codes = []
        if index < len(text) and not text[index].startswith("Level"):
            while (index < len(text) and 
                (not text[index].startswith("Level"))):
                codes = self.add_code(text, index)
                if text[index].startswith("Option"):
                    codes.append(f"Level {level} {text[index]}:{text[index + 1]}")
                    index += 1
                index += 1
            option[level] = codes
        else:
            index += 1
 
        text = text[index:]
        return core, option, conversion, text
    

    def find_units(self) -> dict:
        """ Given the url of the course, fetch all the units outlined.
        """        
        text = self.text
        #cut out only the units in the course structure
        if "Accreditation" in text:
            text = text[text.index("Course structure details"):text.index("Accreditation")]
        elif "Course accreditation" in text:
            text = text[text.index("Course structure details"):text.index("Course accreditation")]
        
        #keeps the list of conversion, core and option units
        core, option, conversion = {}, {}, {}
        
        #up to 5 levels
        for level in range(1, 6):
            core, option, conversion, text = self.get_units(core, option, conversion, level, text)

        return conversion, core, option






def url_check(code):
    """check the code data from web"""
    response = requests.get(UnitList.URL + code)
    soup = BeautifulSoup(response.text, "html.parser")
    return [s.strip() for s in soup.get_text().splitlines() if s.strip()]


if __name__ == "__main__":
    ##################
    ###    UNIT    ###
    ##################
    # # you can make your own unit by providing the unit code as follows.
    # # by default it will retrieve the info from the handbook.
    # unit = Unit("CITS1001")

    # # if you have the unit in file, you can load it like this
    # # if it fails, it will try to load from the handbook.
    # unit = Unit()
    # unit = unit.load("CITS1003")

    # # you might want to update the unit with new contents from the handbook   
    # unit = Unit()
    # unit = unit.load("CITS1003")
    # unit.description = "hello."
    # print(unit)
    # unit = unit.update()
    # print(unit)

    # # you can save unit too which uses default name as the code of the unit.
    # # you can edit content and save it using another name.
    # unit = Unit()
    # unit = unit.load("CITS1003")
    # unit.description = "hello."
    # unit.code = "CITS1003b"
    # unit.prereq = "CITS1001 or CITS1401"
    # unit.semester = [2]
    # unit.save("CITS1003b")
    # unit = unit.load("CITS1003b")
    # print(unit)
    # print(unit.prereqlist)
    # print(Unit().load("CITS1003"))
    # print(Unit().load("CITS1003").prereqlist)


    ######################
    ###    UNIT LIST   ###
    ######################
    # # without any parameters, it creats an empty unitlist.
    # # if fname exists, it loads the units from the fname
    # # if you can pass in the list of unit codes as string, it will load those units.
    # # if fname exists, it ignores the input list.
    # unitlist = UnitList()
    # unitlist = UnitList(fname="unit_list.txt")
    # unitlist = UnitList(ulisit=["CITS1003", "CITS1401"])

    # # set your new fname, any changes will be saved here.
    # unitlist.set_fname("new_list.txt")

    # # below code scans all units (e.g., CITS1000 to CITS6000) and saves them
    # # edit the code and stop to discover a subset
    # # this method is used usually first time to populate the units
    # unitlist.find_units('CITS1000', stop="6000")

    # # You can clean up your unit files by calling this
    # # it will go over your current list from unit_list.txt and delete
    # # ones no longer available in the handbook.
    # unitlist.remove_none_units()

    # # You can output the current units as text in the unitlist as follows.
    # # by default it will save to its own file name, but you can specify other names.
    # unitlist.save()
    # unitlist.save("hello.txt")


    ####################
    ###    COURSE    ###
    ####################
    # # you can create an empty course and populate it later
    # course = Course()

    # # you can create the course from giving a URL
    # course = Course(url="https://www.uwa.edu.au/study/Courses/International-Cybersecurity")
    # course = Course(url="https://www.uwa.edu.au/study/Courses/Artificial-Intelligence")
    # course = Course(url="https://www.uwa.edu.au/study/Courses/Computing-and-Data-Science")
    # course = Course(url="https://www.uwa.edu.au/study/Courses/Software-Engineering")
    # course = Course(url="https://www.uwa.edu.au/study/courses/master-of-information-technology")
    # MPE import needs work...
    # course = Course(url="https://www.uwa.edu.au/study/courses/master-of-professional-engineering")
    
    # # you can also load courses from saved course files
    # course = Course()
    # course = course.load("Artificial Intelligence")
    # print(course)
    # # update the course units' contentsx from handbook by updating
    # course.update()

    # # you can save courses using the save method.
    # # the title is used as the file name, unless provided
    # course.save()
    # course.save("some_name")







    pass



def url_check(url, code):
    """check the code data from web"""
    response = requests.get(url + code)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text().strip()
    return " ".join([s.strip() for s in text.splitlines() if s.strip()])

def match_code(text):
    pattern = r'\b[a-zA-Z]{4}\d{4}\b|\b6 points\b|\b12 points\b|\b24 points\b|\b36 points\b|\b48 points\b'
    matches = re.findall(pattern, text)
    return matches  

def is_code(ucode):
    """check if ucode is actually code"""
    return (len(ucode) == 8 and 
            ucode[4:].isnumeric() and
            ucode[:4].isalpha())


CURL = ""
text = url_check(CURL, "")

if "Master of Professional Engineering" in text:
    prem = text[text.index("Course structure details"):
                text.index("Biomedical Engineering specialisation")]
    after = text[text.index("Software Engineering specialisation"):
                 text.index("Meet our students")]
    after = after.replace("Take unit(s) to the value of 36 points", "Option - Take unit(s) to the value of 36 points")
    text = prem + " " + after
elif "Software Engineering major units." in text:
    text = text[text.index("Software Engineering major units."):text.index("Course structure details Your degree options")]
elif "Accreditation" in text:
    text = text[text.index("Course structure details"):text.index("Accreditation")]
elif "Course accreditation" in text:
    text = text[text.index("Course structure details"):text.index("Course accreditation")]


# print("***")
# print(text)
# print("***")

text = text.replace("Honours", "")

if "Level" in text:
    textlist = text.split("Level")[1:]
    if "Option" in text:
        textlist = [text.strip().split("Option") for text in textlist]
    else:
        textlist = [[text] for text in textlist]
elif "Conversion" in text: #works for MIT
    textlist = [t.split("Option") for t in text.split("Core")]
level = 0
conv, brid, core, opt = {}, {}, {}, {}


# print("***")
# print(textlist)
# print("***")
# # input()

for text in textlist:
    options = []
    for i in range(len(text)):
        if any(["Conversion" in t for t in text]):
            conv[level] = match_code(text[0])
            continue
        elif level == 0:
            level += 1
        if "Bridging" in text[i]:
            brid[level] = match_code(" ".join(text[i].split("Bridging")[1:]))
            text[i] = " ".join(text[i].split("Bridging")[:1])
        if i == 0:
            core[level] = [code for code in match_code(text[i]) if is_code(code)]

        else:
            option = match_code(text[i])
            # option = get_relevant_text(PREFIX, text[i])
            options.append(option)
    opt[level] = options

    print(f"Level {level} Done!")
    level += 1


