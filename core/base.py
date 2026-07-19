
import random
from dataclasses import dataclass


@dataclass
class Time:
    hour: int
    minute: int
    second: float
    
    def __repr__(self):
        return self.to_str()
    
    def __mul__(self, other: int):
        return Time(self.hour * other, self.minute * other, self.second * other) + 0
    
    def __add__(self, other: "Time | int"):
        time = self.copy()
        
        if isinstance(other, Time):
            time.hour += other.hour
            time.minute += other.minute
            time.second += other.second
        elif isinstance(other, int):
            time.second = other
        else:
            raise TypeError(f"Cannot add {type(other)} to Time")
        
        time.normalize()
        
        return time
    
    def __radd__(self, other):
        self.__add__(other)
    
    def __rmul__(self, other):
        self.__mul__(other)

    def in_seconds(self):
        return self.second + self.minute * 60 + self.hour * 60 * 60
    
    def in_minutes(self):
        return self.in_seconds() / 60
    
    def in_hours(self):
        return self.in_minutes() / 60
    
    def to_str(self):
        return f"{"0" if self.hour < 10 else ""}{self.hour}:{"0" if self.minute < 10 else ""}{self.minute}:{"0" if self.second < 10 else ""}{self.second}"
    
    def normalize(self):
        min_add = self.hour % 1
        
        # Hour
        _carry = int(self.hour // 24)
        
        if _carry:
            if not hasattr(self, "_carry"):
                self._carry = 0
            
            self._carry += int(self.hour // 24)
        
        self.hour //= 1
        self.hour %= 24
        
        # Minutes
        self.minute += min_add * 60
        
        sec_add = self.minute % 1
        
        self.hour += self.minute // 60
        
        self.minute //= 1
        self.minute %= 60
        
        self.minute = int(self.minute)
        
        # Seconds
        self.second += sec_add * 60
        
        self.minute += self.second // 60
        
        self.second %= 60
        
        self.hour = int(self.hour)
        self.minute = int(self.minute)
        if self.second % 1 == 0:
            self.second = int(self.second)
        
        if self.hour >= 24 or self.minute >= 60:
            self.normalize()
    
    @staticmethod
    def str_to_time(str_time: str):
        hour, min, sec = str_time.split()[3].split(":")
        
        return Time(int(hour), int(min), int(sec))
    
    def copy(self):
        return Time(self.hour, self.minute, self.second)

@dataclass
class Period:
    time: Time
    day: str
    date: int
    month: str
    year: int
    
    def __repr__(self):
        return self.to_str()
    
    def in_seconds(self):
        prev_months = list(MONTHS_OF_THE_YEAR.values())[:list(MONTHS_OF_THE_YEAR).index(self.month)] + [0]
        
        days = sum(prev_months) + self.date - 1
        
        return self.time.in_seconds() + days * 24 * 60 * 60
    
    def in_minutes(self):
        return self.in_seconds() / 60
    
    def in_hours(self):
        return self.in_minutes() / 60
    
    def in_days(self):
        return self.in_hours() / 24
    
    def in_weeks(self):
        return self.in_days() / 7
    
    def normalize(self):
        self.time.normalize()
        
        _time_carry = 0
        if hasattr(self.time, "_carry"):
            _time_carry = self.time._carry
        
        self.date += _time_carry
        
        orig_date = self.date
        
        m_list = list(MONTHS_OF_THE_YEAR)
        
        m_index = m_list.index(self.month)
        day_index = (DAYS_OF_THE_WEEK.index(self.day) + _time_carry) % 7
        
        self.day = DAYS_OF_THE_WEEK[day_index]
        
        if self.date > MONTHS_OF_THE_YEAR[self.month]:
            self.date -= MONTHS_OF_THE_YEAR[self.month]
            
            self.month = m_list[(m_index + 1) % len(MONTHS_OF_THE_YEAR)]
            
            if m_index == len(MONTHS_OF_THE_YEAR) - 1:
                self.year += 1
            
            self.day = DAYS_OF_THE_WEEK[(day_index + (MONTHS_OF_THE_YEAR[self.month] + self.date - orig_date) % 7) % 7]
        elif self.date < 1:
            self.date += MONTHS_OF_THE_YEAR[self.month]
            
            self.month = m_list[m_index - 1]
            
            if m_index == 0:
                self.year -= 1
            
            self.day = DAYS_OF_THE_WEEK[(day_index - abs(orig_date - 1) % 7) % 7]
        
        if hasattr(self.time, "_carry"):
            del self.time._carry
    
    @staticmethod
    def str_to_period(str_time: str):
        day, month, date, _, year = str_time.split()
        
        day = next((dotw for dotw in DAYS_OF_THE_WEEK if day in dotw))
        month = next((moty for moty in MONTHS_OF_THE_YEAR if month in moty))
        date = int(date)
        year = int(year)
        
        return Period(Time.str_to_time(str_time), day, date, month, year)
    
    def to_str(self):
        return f"{self.time.to_str()} {self.day} {positionify(self.date)} {self.month} {self.year}"
    
    def copy(self):
        return Period(self.time.copy(), self.day, self.date, self.month, self.year)



DAYS_OF_THE_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_OF_THE_YEAR = {
    "January": 31,
    "February": 29,
    "March": 31,
    "April": 30,
    "May": 31,
    "June": 30,
    "July": 31,
    "August": 31,
    "September": 30,
    "October": 31,
    "November": 30,
    "December": 31,
}

def positionify(number: int | str, default: str | None = ...):
    if isinstance(number, int):
        number = str(number)
    
    suffix = ("st" if number.endswith("1") and number != "11" else ("nd" if number.endswith("2") and number != "12" else "rd" if number.endswith("3") and number != "13" else "th"))
    
    if not number.isnumeric():
        if not isinstance(default, ellipsis):
            suffix = (default if default is not None else "")
        else:
            raise Exception(f"Text: ({number}) is not numeric")
        
    return number + suffix

S_DAY = Time(24, 0, 0).in_seconds()
S_WEEK = S_DAY * 7
def S_MONTH(month: str):
    return S_DAY * MONTHS_OF_THE_YEAR[month]
S_YEAR = S_DAY * 365



class ID(str):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        self.parents: list[ID] = []
    
    def __add__(self, value):
        id = ID(value)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        if self == other:
            id = self.parents[-1]
        else:
            self.parents.remove(other)
            
            for p in self.parents:
                if p.parents == self.parents:
                    id = p
                    break
            else:
                id = self
        
        return id
    
    def __rsub__(self, other):
        return self.__sub__(other)
    
    @staticmethod
    def new():
        tmp = random.randint(0, 500000)
        
        return ID(id(tmp))

class CLASS_ID(ID):
    def __init__(self, *args, class_level_id: ID = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        assert class_level_id is not None
        
        self.class_level_id = class_level_id
    
    def __add__(self, value):
        if isinstance(value, CLASS_ID):
            assert self.class_level_id == value.class_level_id
        
        id = CLASS_ID(value, class_level_id=self.class_level_id)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    @staticmethod
    def new(class_level_id):
        tmp = random.randint(0, 500000)
        
        return CLASS_ID(id(tmp), class_level_id=class_level_id)



