from ..models import Cashinbanks, Depositaccount, Adjentry, Preamt, Exchangerate, Report, Account, Company, Group, Reltrx, Distitle, Disdetail, Disclosure
import math

def normal_round(amt):
        if amt/1000 - math.floor(amt/1000) < 0.5:
            return math.floor(amt/1000)
        else:
            return math.ceil(amt/1000)