import pandas as pd 
import numpy as np  
from scipy import stats
import matplotlib.pyplot as plt


def AdjustTestStatistic(n, D):
    return (np.sqrt(n) + .12 + (.11/np.sqrt(n))) * D


df = pd.read_excel('Experiment1.xlsx', index_col=None)
list(df)

# Conduct K-S Tests for each sample (n=500) to ensure standard uniform distribution of Blue Com Risk 

for i in range(1, 11, 1):
    if i == 3:RED_TGT_EFF = .3
    else:    RED_TGT_EFF = i *.1
        
    df2 = df.loc[df.RedTgt==RED_TGT_EFF]

    bluecom = np.array(df2.BlueCom)
    Dn = stats.kstest(bluecom, 'uniform')[0] #scipy unniform distribution defaults to standard U(0,1)
    AdjD = AdjustTestStatistic(500, Dn)
    print("RED Targeting Effectiveness = ", RED_TGT_EFF)
    print("Adjusted Test Statistic ", AdjD)
    KSTest = "Failed to Reject H0" if AdjD <= 1.358 else "Reject H0"
    print("KSTest Test for Standard Uniform Distribution at Alpha.05 - ", KSTest)
    print("")
    plt.hist(bluecom)
    plt.title("RED_TGT_EFF = " + str(RED_TGT_EFF))
    plt.show()


#conduct scatter plot analysis of Red Targeting Effectiveness to KPIs

plt.scatter(df.RedTgt, df['Total Steps'])
plt.title("Red Targeting vs Total Steps")
plt.show()
print("(Pearson) Correclation Coef = ",df.RedTgt.corr(df['Total Steps']))
print("")

plt.scatter(df.RedTgt, df['Blue Total Attrition'])
plt.title("Red Targeting vs Blue Attrition")
plt.show()
print("(Pearson) Correclation Coef = ",df.RedTgt.corr(df['Blue Total Attrition']))
print("")

plt.scatter(df.RedTgt, df['Blue Final Effectiveness'])
plt.title("Red Targeting vs Blue Final Effectiveness")
plt.show()
print("(Pearson) Correclation Coef = ",df.RedTgt.corr(df['Blue Final Effectiveness']))


#conduct scatter plot analysis of Red Targeting Effectiveness to KPIs

plt.scatter(df.BlueCom, df['Total Steps'])
plt.title("Blue Communication vs Total Steps")
plt.show()
print("(Pearson) Correclation Coef = ",df.BlueCom.corr(df['Total Steps']))
print("")

plt.scatter(df.BlueCom, df['Blue Total Attrition'])
plt.title("Blue Communication vs Blue Attrition")
plt.show()
print("(Pearson) Correclation Coef = ",df.BlueCom.corr(df['Blue Total Attrition']))
print("")

plt.scatter(df.BlueCom, df['Blue Final Effectiveness'])
plt.title("Blue Communication vs Blue Final Effectiveness")
plt.show()
print("(Pearson) Correclation Coef = ",df.BlueCom.corr(df['Blue Final Effectiveness']))
print("")
