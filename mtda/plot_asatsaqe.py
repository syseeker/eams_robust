from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from matplotlib.dates import WEEKLY, DAILY, HOURLY, MINUTELY, rrulewrapper, RRuleLocator
from matplotlib import rc
import matplotlib.gridspec as gridspec
import numpy as np

def _getPlotRule(ptype):         
    if ptype == 0:
        return MINUTELY
    if ptype == 1:
        return HOURLY
    if ptype == 2:
        return DAILY
    if ptype == 3:
        return WEEKLY
    else:
        print "Unknown Plot Type. Set to default DAILY"
        return DAILY
    
def writeSingleRoom(fdir, fname, pslot, pt, ptsa, ptoa, pasa, pqp, pqs, ptotal):
    f = open(fdir+fname,'w')
    f.write(",".join(map(str, pslot)))
    f.write("\n")
    f.write(",".join(map(str, pt)))
    f.write("\n")
    f.write(",".join(map(str, ptsa)))
    f.write("\n")
    f.write(",".join(map(str, pasa)))
    f.write("\n")
    f.write(",".join(map(str, ptoa)))
    f.write("\n")
    f.write(",".join(map(str, pqs)))
    f.write("\n")
    f.write(",".join(map(str, pqp)))
    f.write("\n")
    f.write(",".join(map(str, ptotal)))
    f.write("\n")
    f.close()
                    
def plotMultiRooms(fdir, fname, pinterval, pstep, pslot, arr_t, arr_tsa, ptoa, arr_asa, arr_qp, arr_qs, arr_total, notes):
         
    rc('mathtext', fontset='stixsans') 
     
    colors = ['r','g','b','m']
    lines = ['--', '-', '.']
      
    fig = plt.figure()
    gs = gridspec.GridSpec(5, 1)  #, wspace=0.0, hspace=0.0
    gs.update(hspace=0.1)
    efig = fig.add_subplot(gs[0,:])
    qfig = fig.add_subplot(gs[1,:])
    afig = fig.add_subplot(gs[2,:])
    tfig = fig.add_subplot(gs[3:,0])
    
    efig.set_title(notes + "\n Energy:" + str(round(np.sum(arr_total),2)) + " kWh", fontsize=8)
    for i in xrange(len(arr_total)):
        efig.plot(pslot, arr_total[i], color=colors[i], label='R'+str(i))
    efig.grid(True)
    efig.set_ylabel("Electricity (kWh)", fontsize=8)
#     efig.set_ylim([0.0,5.0])
#     efig.set_ylim([0.0,35.0])
    handles, labels = efig.get_legend_handles_labels()
    fontP = FontProperties()
    fontP.set_size(6)
    efig.legend(handles, labels, ncol=4, loc='best', prop=fontP)
     
    for i in xrange(len(arr_qp)):
        if i==0:
            qfig.plot(pslot, arr_qp[i], lines[0], color=colors[i], label='Q$^{\mathrm{p}}$')
            qfig.plot(pslot, arr_qs[i], lines[1], color=colors[i], label='Q$^{\mathrm{s}}$')
        else:
            qfig.plot(pslot, arr_qp[i], lines[0], color=colors[i])
            qfig.plot(pslot, arr_qs[i], lines[1], color=colors[i])
    qfig.grid(True)
    qfig.set_ylabel("Heat Gain (kW)", fontsize=8)
    qfig.set_ylim([0.0,1.5])
    handles, labels = qfig.get_legend_handles_labels()
    fontP = FontProperties()
    fontP.set_size(6)
    qfig.legend(handles, labels, loc='best', prop=fontP) 
      
    for i in xrange(len(arr_asa)):
        if i==0:
            afig.plot(pslot, arr_asa[i], color=colors[i], label='ASA')
        else:
            afig.plot(pslot, arr_asa[i], color=colors[i])
    afig.grid(True)
    afig.set_ylabel("Air Flow Rate (kg/s)", fontsize=8)
#     afig.set_ylim([0.0,1.0])
    afig.set_ylim([0.0,5.0])
    handles, labels = afig.get_legend_handles_labels()
    fontP = FontProperties()
    fontP.set_size(6)
    afig.legend(handles, labels, loc='best', prop=fontP) 
    
  
    tfig.plot(pslot, ptoa, 'gray', label='Outdoor')
#     tfig.plot(pslot, [21]*len(pslot), 'y-', label='Comfort Bounds')
#     tfig.plot(pslot, [23]*len(pslot), 'y-')    
    for i in xrange(len(arr_tsa)):
        tfig.plot(pslot, arr_tsa[i], lines[0], color=colors[i], label='TSA$^{\mathrm{ R1}}$ R'+str(i))
        tfig.plot(pslot, arr_t[i], lines[1], color=colors[i], label='T$^{\mathrm{ R1}}$ R'+str(i))
    tfig.grid(True)
    tfig.set_ylabel("Temperature ($\circ$C)", fontsize=8)
#     tfig.set_ylim([0,45])
    tfig.set_xlabel("Scheduling Periods", fontsize=8)
    handles, labels = tfig.get_legend_handles_labels()
    fontP = FontProperties()
    fontP.set_size(8)
    tfig.legend(handles, labels, ncol=5, loc='best', prop=fontP)
      
    ymdhFmt = mdates.DateFormatter('%Y-%m-%d %H:%M')
    rule_1 = rrulewrapper(_getPlotRule((int)(pinterval)), interval=(int)(pstep)) 
    loc_1 = RRuleLocator(rule_1)
    tfig.xaxis.set_major_locator(loc_1)    
    tfig.xaxis.set_major_formatter(ymdhFmt)
    datemin = datetime(min(pslot).year, min(pslot).month, min(pslot).day, min(pslot).hour, min(pslot).minute) 
    datemax = datetime(max(pslot).year, max(pslot).month, max(pslot).day, max(pslot).hour, max(pslot).minute)
    tfig.set_xlim(datemin, datemax)  
          
    plt.setp(efig.get_yticklabels(), fontsize=8)
    plt.setp(qfig.get_yticklabels(), fontsize=8)
    plt.setp(afig.get_yticklabels(), fontsize=8)
    plt.setp(tfig.get_yticklabels(), fontsize=8)
      
    efig.get_xaxis().set_visible(False)
    qfig.get_xaxis().set_visible(False) 
    afig.get_xaxis().set_visible(False)  
    plt.setp(tfig.get_xticklabels(), rotation='30', ha='right', fontsize=8)
 
#     plt.show()
    plt.savefig(fdir + fname+'.png', dpi=400)
    plt.close()
     
     

def plotBounds(fdir, fname, pinterval, pstep, pslot, arr_t, ptoa, arr_total, arr_tslacklb, arr_tslackub, arr_tcaplb, arr_tcapub, arr_tlb, arr_tub, notes):
    
    rc('mathtext', fontset='stixsans') 
    
    colors = ['r','g','b','m']
    lines = ['x', '-', '.']
      
    fig = plt.figure()
    gs = gridspec.GridSpec(4, 1)
    gs.update(hspace=0.1)
    sfig = fig.add_subplot(gs[0,:])
    cfig = fig.add_subplot(gs[1,:])
    tfig = fig.add_subplot(gs[2:,0])
    
    sfig.set_title(notes + "\n Energy:" + str(round(np.sum(arr_total),2)) + " kWh", fontsize=8)
    for i in xrange(len(arr_tslacklb)):
        sfig.plot(pslot, arr_tslacklb[i], lines[0], color=colors[i], label='R'+str(i))
        sfig.plot(pslot, arr_tslackub[i], lines[1], color=colors[i], label='R'+str(i))
    sfig.grid(True)
    sfig.set_ylabel("xi", fontsize=8)
    handles, labels = sfig.get_legend_handles_labels()
    fontP = FontProperties()
    fontP.set_size(6)
    sfig.legend(handles, labels, loc='best', prop=fontP)

    for i in xrange(len(arr_tcaplb)):
        cfig.plot(pslot, arr_tcaplb[i], lines[0], color=colors[i], label='R'+str(i))
        cfig.plot(pslot, arr_tcapub[i], lines[0], color=colors[i], label='R'+str(i))
    cfig.grid(True)
    cfig.set_ylabel("$\widehat{T}$", fontsize=8)
        
    tfig.plot(pslot, ptoa, 'gray', label='Outdoor')
    for i in xrange(len(arr_tub)):
        tfig.plot(pslot, arr_tub[i], lines[0], color=colors[i], label='TUB R'+str(i))
        tfig.plot(pslot, arr_tlb[i], lines[1], color=colors[i], label='TLB R'+str(i))
        tfig.plot(pslot, arr_t[i], lines[2], color=colors[i], label='T R'+str(i))
    tfig.grid(True)
    tfig.set_ylabel("Temperature ($\circ$C)", fontsize=8)
    tfig.set_xlabel("Scheduling Periods", fontsize=8)
    handles, labels = tfig.get_legend_handles_labels()
    fontP = FontProperties()
    fontP.set_size(8)
    tfig.legend(handles, labels, ncol=5, loc='best', prop=fontP)
      
    ymdhFmt = mdates.DateFormatter('%Y-%m-%d %H:%M')
    rule_1 = rrulewrapper(_getPlotRule((int)(pinterval)), interval=(int)(pstep)) 
    loc_1 = RRuleLocator(rule_1)
    tfig.xaxis.set_major_locator(loc_1)    
    tfig.xaxis.set_major_formatter(ymdhFmt)
    datemin = datetime(min(pslot).year, min(pslot).month, min(pslot).day, min(pslot).hour, min(pslot).minute) 
    datemax = datetime(max(pslot).year, max(pslot).month, max(pslot).day, max(pslot).hour, max(pslot).minute)
    tfig.set_xlim(datemin, datemax)  
          
    plt.setp(sfig.get_yticklabels(), fontsize=8)
    plt.setp(cfig.get_yticklabels(), fontsize=8)    
    plt.setp(tfig.get_yticklabels(), fontsize=8)
      
    sfig.get_xaxis().set_visible(False)
    cfig.get_xaxis().set_visible(False)
    plt.setp(tfig.get_xticklabels(), rotation='30', ha='right', fontsize=8)
 
#     plt.show()
    plt.savefig(fdir + fname+'.png', dpi=400)
    plt.close()
    
    
    
    
