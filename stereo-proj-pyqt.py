#!/usr/bin/python

######################################################################
#
#
# Stereo-Proj is a python utility to plot stereographic projetion of a given crystal. It is designed
# to be used in electron microscopy experiments.
# Author: F. Mompiou, CEMES-CNRS
#
#######################################################################


from __future__ import division
import numpy as np
from PyQt4 import QtGui, QtCore
import sys
import random
import os
from PIL  import Image
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt
import matplotlib as mpl
import stereoprojUI
import intersectionsUI
import angleUI
import schmidUI
import xyzUI
import widthUI
                 
#font size on plot 
mpl.rcParams['font.size'] = 12

################
#       Misc
################

def unique_rows(a):
    a = np.ascontiguousarray(a)
    unique_a = np.unique(a.view([('', a.dtype)]*a.shape[1]))
    return unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))
    


###################################################################"
##### Projection
####################################################################

def proj(x,y,z): 
  
    if z==1: 
        X=0
        Y=0
    elif z<-0.000001:
        X='nan'
        Y='nan'
    else: 
            
        X=x/(1+z)
        Y=y/(1+z)
    
    return np.array([X,Y],float) 

def proj2(x,y,z): 
  
    if z==1: 
        X=0
        Y=0
    elif z<-0.000001:
        X=-x/(1-z)
        Y=-y/(1-z)
    else: 
            
        X=x/(1+z)
        Y=y/(1+z)
    
    return np.array([X,Y,z],float)     
###################################################################
# Rotation Euler
#
##################################################################

def rotation(phi1,phi,phi2):
   phi1=phi1*np.pi/180;
   phi=phi*np.pi/180;
   phi2=phi2*np.pi/180;
   R=np.array([[np.cos(phi1)*np.cos(phi2)-np.cos(phi)*np.sin(phi1)*np.sin(phi2),
            -np.cos(phi)*np.cos(phi2)*np.sin(phi1)-np.cos(phi1)*
            np.sin(phi2),np.sin(phi)*np.sin(phi1)],[np.cos(phi2)*np.sin(phi1)
            +np.cos(phi)*np.cos(phi1)*np.sin(phi2),np.cos(phi)*np.cos(phi1)
            *np.cos(phi2)-np.sin(phi1)*np.sin(phi2), -np.cos(phi1)*np.sin(phi)],
            [np.sin(phi)*np.sin(phi2), np.cos(phi2)*np.sin(phi), np.cos(phi)]],float)
   return R

###################################################################
# Rotation around a given axis
#
##################################################################

def Rot(th,a,b,c):
   th=th*np.pi/180;
   aa=a/np.linalg.norm([a,b,c]);
   bb=b/np.linalg.norm([a,b,c]);
   cc=c/np.linalg.norm([a,b,c]);
   c1=np.array([[1,0,0],[0,1,0],[0,0,1]],float)
   c2=np.array([[aa**2,aa*bb,aa*cc],[bb*aa,bb**2,bb*cc],[cc*aa,
                cc*bb,cc**2]],float)
   c3=np.array([[0,-cc,bb],[cc,0,-aa],[-bb,aa,0]],float)
   R=np.cos(th)*c1+(1-np.cos(th))*c2+np.sin(th)*c3

   return R    

#######################
#
# Layout functions
#
#######################

def color_trace():
        color_trace=1
        if ui.color_trace_bleu.isChecked():
                color_trace=1
        if ui.color_trace_bleu.isChecked():
                color_trace=2
        if ui.color_trace_rouge.isChecked():
                color_trace=3
        return color_trace

def var_uvw():
        var_uvw=0
        if ui.uvw_button.isChecked():
                var_uvw=1
        
        return var_uvw

def var_hexa():
        var_hexa=0
        if ui.hexa_button.isChecked():
                var_hexa=1
        
        return var_hexa

def var_carre():
        var_carre=0
        if ui.style_box.isChecked():
                var_carre=1
        
        return var_carre

####################################################################
#
#  Crystal definition
#
##################################################################

def crist():
    global axes,axesh,D,Dstar,V
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alpha=np.float(ui.alpha_entry.text())
    beta=np.float(ui.beta_entry.text())
    gamma=np.float(ui.gamma_entry.text())
    e=np.int(ui.e_entry.text())
    d2=np.float(ui.d_label_var.text())
    alpha=alpha*np.pi/180;
    beta=beta*np.pi/180;
    gamma=gamma*np.pi/180;
    V=a*b*c*np.sqrt(1-(np.cos(alpha)**2)-(np.cos(beta))**2-(np.cos(gamma))**2+2*np.cos(alpha)*np.cos(beta)*np.cos(gamma))
    D=np.array([[a,b*np.cos(gamma),c*np.cos(beta)],[0,b*np.sin(gamma),  c*(np.cos(alpha)-np.cos(beta)*np.cos(gamma))/np.sin(gamma)],[0,0,V/(a*b*np.sin(gamma))]])
    Dstar=np.transpose(np.linalg.inv(D))
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])    
    axes=np.zeros(((2*e+1)**3-1,3))
    axesh=np.zeros(((2*e+1)**3-1,5))
    axesh[:,4]=color_trace()
    id=0
    for i in range(-e,e+1):
        for j in range(-e,e+1):
            for k in range(-e,e+1):
                if (i,j,k)!=(0,0,0):
                    d=1/(np.sqrt(np.dot(np.array([i,j,k]),np.dot(np.linalg.inv(G),np.array([i,j,k])))))
                    if d>d2*0.1*np.amax([a,b,c]):
                        if var_uvw()==0:                    
                            Ma=np.dot(Dstar,np.array([i,j,k],float))
                            axesh[id,0]=Ma[0]
                            axesh[id,1]=Ma[1]
                            axesh[id,2]=Ma[2]
                            axesh[id,3]=0
                            axes[id,:]=np.array([i,j,k],float)
                        else:
                            Ma=np.dot(D,np.array([i,j,k],float))
                            axesh[id,0]=Ma[0]
                            axesh[id,1]=Ma[1]
                            axesh[id,2]=Ma[2]
                            axesh[id,3]=1
                            axes[id,:]=np.array([i,j,k],float)
                        id=id+1
                    
    return axes,axesh,D,Dstar,V

######################################################
#
# Reduce number of poles/directions as a function of d-spacing (plus or minus)
#
#######################################################

def dm():
    global dmip,a,minx,maxx,miny,maxy
    
    dmip=dmip-np.float(ui.d_entry.text())
    ui.d_label_var.setText(str(dmip))
    crist()
    trace()
    
    return dmip
    
def dp():
    global dmip, a

    dmip=dmip+np.float(ui.d_entry.text())
    ui.d_label_var.setText(str(dmip))
    crist()    
    trace()
    
    return dmip 
    

    
####################################################################
#
#  Plot iso-schmid factor, ie for a given plan the locus of b with a given schmid factor (Oy direction
# assumed to be the straining axis
#
####################################################################

def schmid_trace():
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid,a,minx,maxx,miny,maxy,trC
    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
        
    tr_schmid=np.vstack((tr_schmid,np.array([pole1,pole2,pole3])))
    trace()
    
def undo_schmid_trace():
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid,a,minx,maxx,miny,maxy,trC
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    tr_s=tr_schmid
    for i in range(1,tr_schmid.shape[0]):
		if tr_schmid[i,0]==pole1 and tr_schmid[i,1]==pole2 and tr_schmid[i,2]==pole3:
			tr_s=np.delete(tr_schmid,i,0)
    tr_schmid=tr_s
    trace()

def fact(angle,r,t,n):
	x=r*np.cos(t)/n
	y=r*np.sin(t)/n
	f=np.cos(angle)*2*y/((1+x**2+y**2))
	return f    

def schmid_trace2(C):
    global D, Dstar,M,a
    for h in range(1,tr_schmid.shape[0]):
        b1=C[h,0]   
        b2=C[h,1]   
        b3=C[h,2]   
        b=np.array([b1,b2,b3])
        
        if var_uvw()==0: 
            bpr=np.dot(Dstar,b)/np.linalg.norm(np.dot(Dstar,b))
        else:
            bpr=np.dot(Dstar,b)/np.linalg.norm(np.dot(Dstar,b))
		  
        bpr2=np.dot(M,bpr)
        T=np.array([0,1,0])
        angleb=np.arccos(np.dot(bpr2,T)/np.linalg.norm(bpr2))
        n=300
        r=np.linspace(0,n,100)
        t=np.linspace(0,2*np.pi,100)
        r,t=np.meshgrid(r,t)
        F=fact(angleb,r,t,n)
        lev=[-0.5,-0.4,-0.3,-0.2,0.2,0.3,0.4,0.5]
        CS=a.contour(r*np.cos(t)+300, r*np.sin(t)+300, F,lev,linewidths=2)
        fmt = {}
        strs = [ '('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') -0.5','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') -0.4','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') -0.3','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') -0.2','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') 0.2','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') 0.3','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') 0.4','('+str(np.int(b1))+str(np.int(b2))+str(np.int(b3))+') 0.5']
        for l,s in zip( CS.levels, strs ):
			fmt[l] = s
	a.clabel(CS,fmt=fmt,fontsize=10,inline=True)						

    
###########################################################################
#
# Rotation of the sample. If Lock Axes is off rotation are along y,x,z directions. If not, the y and z axes 
# of the sample are locked to the crystal axes when the check box is ticked. It mimics double-tilt holder (rotation of alpha along fixed x and rotation of beta along the beta tilt moving axis) or  tilt-rotation holder  (rotation of alpha along fixed # x and rotation of z along the z-rotation moving axis).
#
##########################################################################

def lock():
	global M, var_lock,M_lock
        
        if ui.lock_checkButton.isChecked():
                var_lock=1
                M_lock=M
        else:
        	var_lock,M_lock=0,0

        return var_lock,M_lock


def rot_alpha_p():
    global angle_alpha,M,a,trP,trC

    tha=np.float(ui.angle_alpha_entry.text())
    M=np.dot(Rot(tha,0,1,0),M)
    trace()
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    
    ui.angle_euler_label.setText(t)
    angle_alpha=angle_alpha+np.float(ui.angle_alpha_entry.text())
    ui.angle_alpha_label_2.setText(str(angle_alpha))
    return angle_alpha,M
    
    
def rot_alpha_m():
    global angle_alpha,M,a,trP,trC

    tha=-np.float(ui.angle_alpha_entry.text())
    M=np.dot(Rot(tha,0,1,0),M)
    trace()
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    
    ui.angle_euler_label.setText(t)
    angle_alpha=angle_alpha-np.float(ui.angle_alpha_entry.text())
    ui.angle_alpha_label_2.setText(str(angle_alpha))
    return angle_alpha,M

    
def rot_beta_m():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock
   
    if var_lock==0:
    	AxeY=np.array([1,0,0])
    else:
   	A=np.dot(np.linalg.inv(M_lock),np.array([1,0,0]))
	C=np.dot(np.linalg.inv(Dstar),A)
	AxeY=C/np.linalg.norm(C)
    	AxeY=np.dot(M,AxeY)
    
    thb=-np.float(ui.angle_beta_entry.text())
    M=np.dot(Rot(thb,AxeY[0],AxeY[1],AxeY[2]),M)
    trace()
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    ui.angle_euler_label.setText(t)
    angle_beta=angle_beta-np.float(ui.angle_beta_entry.text())
    ui.angle_beta_label_2.setText(str(angle_beta))
    return angle_beta,M   
   
def rot_beta_p():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock
   
    if var_lock==0:
    	AxeY=np.array([1,0,0])
    else:
   	A=np.dot(np.linalg.inv(M_lock),np.array([1,0,0]))
	C=np.dot(np.linalg.inv(Dstar),A)
	AxeY=C/np.linalg.norm(C)
    	AxeY=np.dot(M,AxeY)
    
    thb=np.float(ui.angle_beta_entry.text())
    M=np.dot(Rot(thb,AxeY[0],AxeY[1],AxeY[2]),M)
    trace()
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    ui.angle_euler_label.setText(t)
    angle_beta=angle_beta+np.float(ui.angle_beta_entry.text())
    ui.angle_beta_label_2.setText(str(angle_beta))
    return angle_beta,M   

def rot_z_m():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock
   
    if var_lock==0:
    	AxeZ=np.array([0,0,1])
    else:
   	A=np.dot(np.linalg.inv(M_lock),np.array([0,0,1]))
	C=np.dot(np.linalg.inv(Dstar),A)
	AxeZ=C/np.linalg.norm(C)
    	AxeZ=np.dot(M,AxeZ)
    
    thz=-np.float(ui.angle_z_entry.text())
    M=np.dot(Rot(thz,AxeZ[0],AxeZ[1],AxeZ[2]),M)
    trace()
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    ui.angle_euler_label.setText(t)
    angle_z=angle_z-np.float(ui.angle_z_entry.text())
    ui.angle_z_label_2.setText(str(angle_z))
    return angle_z,M      
   
def rot_z_p():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock
   
    if var_lock==0:
    	AxeZ=np.array([0,0,1])
    else:
   	A=np.dot(np.linalg.inv(M_lock),np.array([0,0,1]))
	C=np.dot(np.linalg.inv(Dstar),A)
	AxeZ=C/np.linalg.norm(C)
    	AxeZ=np.dot(M,AxeZ)
    
    thz=np.float(ui.angle_z_entry.text())
    M=np.dot(Rot(thz,AxeZ[0],AxeZ[1],AxeZ[2]),M)
    trace()
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    ui.angle_euler_label.setText(t)
    angle_z=angle_z+np.float(ui.angle_z_entry.text())
    ui.angle_z_label_2.setText(str(angle_z))
    return angle_z,M      

####################################################################
#
# Rotate around a given pole
#
####################################################################


def rotgm():
    global g,M,Dstar,a

    thg=-np.float(ui.rot_g_entry.text())
    diff1=np.float(ui.diff1_entry.text())
    diff2=np.float(ui.diff2_entry.text())
    diff3=np.float(ui.diff3_entry.text())
    A=np.array([diff1,diff2,diff3])
    Ad=np.dot(Dstar,A)    
    Ap=np.dot(M,Ad)/np.linalg.norm(np.dot(M,Ad))
    M=np.dot(Rot(thg,Ap[0],Ap[1],Ap[2]),M)
    trace()    
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    
    ui.angle_euler_label.setText(t)
    g=g-np.float(ui.rot_g_entry.text())
    ui.rg_label.setText(str(g))
    return g,M
    
def rotgp():
    global g,M,D

    thg=np.float(ui.rot_g_entry.text())
    diff1=np.float(ui.diff1_entry.text())
    diff2=np.float(ui.diff2_entry.text())
    diff3=np.float(ui.diff3_entry.text())
    A=np.array([diff1,diff2,diff3])
    Ad=np.dot(Dstar,A)    
    Ap=np.dot(M,Ad)/np.linalg.norm(np.dot(M,Ad))
    M=np.dot(Rot(thg,Ap[0],Ap[1],Ap[2]),M)
    trace()    
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    
    ui.angle_euler_label.setText(t)
    g=g+np.float(ui.rot_g_entry.text())
    ui.rg_label.setText(str(g))
    return g,M

###################################################
#
# Mirror the sample
#
#############################################

#def mirror():
#    global M,a,trP,trC
##    a = figure.add_subplot(111)     
##    a.figure.clear()
#    
#    M_r=np.array([[1,0,0],[0,1,0],[0,0,-1]])
#    M=np.dot(M_r,M)
#    trace()
#    phir=np.arccos(M[2,2])*180/np.pi
#    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
#    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
#    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
#    
#    ui.angle_euler_label.setText(t)
#    
#    return M


####################################################################
#
# Add a given pole and equivalent ones
#
####################################################################

def pole(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar
    
    if var_hexa()==1:
        if var_uvw()==1:
            pole1a=2*pole1+pole2
            pole2a=2*pole2+pole1
            pole1=pole1a
            pole2=pole2a
    
    Gs=np.array([pole1,pole2,pole3],float)

    if var_uvw()==0:                    
            Gsh=np.dot(Dstar,Gs)/np.linalg.norm(np.dot(Dstar,Gs))
    else:
        Gsh=np.dot(D,Gs)/np.linalg.norm(np.dot(D,Gs))
     
    S=np.dot(M,Gsh)
    if S[2]<0:
        S=-S
        Gsh=-Gsh
        pole1=-pole1
        pole2=-pole2
        pole3=-pole3

    
    axes=np.vstack((axes,np.array([pole1,pole2,pole3])))
    axes=np.vstack((axes,np.array([-pole1,-pole2,-pole3])))
    T=np.vstack((T,np.array([S[0],S[1],S[2]])))
    T=np.vstack((T,np.array([-S[0],-S[1],-S[2]])))
    if var_uvw()==0 :
        axesh=np.vstack((axesh,np.array([Gsh[0],Gsh[1],Gsh[2],0,color_trace()])))
        axesh=np.vstack((axesh,np.array([-Gsh[0],-Gsh[1],-Gsh[2],0,color_trace()])))
    else:
        axesh=np.vstack((axesh,np.array([Gsh[0],Gsh[1],Gsh[2],1,color_trace()])))
        axesh=np.vstack((axesh,np.array([-Gsh[0],-Gsh[1],-Gsh[2],1,color_trace()])))
    return axes,axesh,T

def undo_pole(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar
    
    if var_hexa()==1:
        if var_uvw()==1:
            pole1a=2*pole1+pole2
            pole2a=2*pole2+pole1
            pole1=pole1a
            pole2=pole2a
    
    Gs=np.array([pole1,pole2,pole3],float)

    if var_uvw()==0:                    
            Gsh=np.dot(Dstar,Gs)/np.linalg.norm(np.dot(Dstar,Gs))
    else:
        Gsh=np.dot(D,Gs)/np.linalg.norm(np.dot(D,Gs))
     
    S=np.dot(M,Gsh)
    if S[2]<0:
        S=-S
        Gsh=-Gsh
        pole1=-pole1
        pole2=-pole2
        pole3=-pole3

    
    ind=np.where((axes[:,0]==pole1) & (axes[:,1]==pole2)& (axes[:,2]==pole3))
    indm=np.where((axes[:,0]==-pole1) & (axes[:,1]==-pole2)& (axes[:,2]==-pole3))
    axes=np.delete(axes,ind,0)
    axes=np.delete(axes,indm,0)
    T=np.delete(T,ind,0)
    T=np.delete(T,indm,0)
    if var_uvw()==0 :
        axesh=np.delete(axesh,ind,0)
        axesh=np.delete(axesh,indm,0)
    else:
        axesh=np.delete(axesh,ind,0)
        axesh=np.delete(axesh,indm,0)
    return axes,axesh,T

    
def d(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alpha=np.float(ui.alpha_entry.text())
    beta=np.float(ui.beta_entry.text())
    gamma=np.float(ui.gamma_entry.text())
    alpha=alpha*np.pi/180;
    beta=beta*np.pi/180;
    gamma=gamma*np.pi/180;
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])    
    ds=(np.sqrt(np.dot(np.array([pole1,pole2,pole3]),np.dot(np.linalg.inv(G),np.array([pole1,pole2,pole3])))))
    return ds
    
def addpole_sym():
    global M,axes,axesh,T,V,D,Dstar,G    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alpha=np.float(ui.alpha_entry.text())
    beta=np.float(ui.beta_entry.text())
    gamma=np.float(ui.gamma_entry.text())
    alpha=alpha*np.pi/180;
    beta=beta*np.pi/180;
    gamma=gamma*np.pi/180;
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])     
    v=d(pole1,pole2,pole3)
    
    pole(pole1,pole2,pole3)
    if np.abs(alpha-np.pi/2)<0.001 and np.abs(beta-np.pi/2)<0.001 and np.abs(gamma-2*np.pi/3)<0.001:
        pole(pole1,pole2,pole3)
        pole(pole1,pole2,-pole3)
        pole(pole2,pole1,pole3)
        pole(pole2,pole1,-pole3)
        pole(-pole1-pole2,pole2,pole3)
        pole(-pole1-pole2,pole2,-pole3)
        pole(pole1,-pole1-pole2,pole3)
        pole(pole1,-pole1-pole2,-pole3)
        pole(pole2,-pole1-pole2,pole3)
        pole(pole2,-pole1-pole2,-pole3)
        pole(-pole1-pole2,pole1,pole3)
        pole(-pole1-pole2,pole1,-pole3)

    else:
        if np.abs(d(pole1,pole2,-pole3)-v)<0.001:
                pole(pole1,pole2,-pole3)
        if np.abs(d(pole1,-pole2,pole3)-v)<0.001:
                pole(pole1,-pole2,pole3)
        if np.abs(d(-pole1,pole2,pole3)-v)<0.001:
            pole(-pole1,pole2,pole3)
        if np.abs(d(pole2,pole1,pole3)-v)<0.001:
            pole(pole2,pole1,pole3)
        if np.abs(d(pole2,pole1,-pole3)-v)<0.001:
            pole(pole2,pole1,-pole3)
        if np.abs(d(pole2,-pole1,pole3)-v)<0.001:
            pole(pole2,-pole1,pole3)
        if np.abs(d(-pole2,pole1,pole3)-v)<0.001:
            pole(-pole2,pole1,pole3)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            pole(pole2,pole3,pole1)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            pole(pole2,pole3,-pole1)
        if np.abs(d(pole2,-pole3,pole1)-v)<0.001:
            pole(pole2,-pole3,pole1)
        if np.abs(d(-pole2,pole3,pole1)-v)<0.001:
            pole(-pole2,pole3,pole1)
        if np.abs(d(pole1,pole3,pole2)-v)<0.001:
            pole(pole1,pole3,pole2)
        if np.abs(d(pole1,pole3,-pole2)-v)<0.001:
            pole(pole1,pole3,-pole2)
        if np.abs(d(pole1,-pole3,pole2)-v)<0.001:
            pole(pole1,-pole3,pole2)
        if np.abs(d(-pole1,pole3,pole2)-v)<0.001:
            pole(-pole1,pole3,pole2)
        if np.abs(d(pole3,pole1,pole2)-v)<0.001:
            pole(pole3,pole1,pole2)
        if np.abs(d(pole3,pole1,-pole2)-v)<0.001:
            pole(pole3,pole1,-pole2)
        if np.abs(d(pole3,-pole1,pole2)-v)<0.001:
            pole(pole3,-pole1,pole2)
        if np.abs(d(-pole3,pole1,pole2)-v)<0.001:
            pole(-pole3,pole1,pole2)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            pole(pole3,pole2,pole1)
        if np.abs(d(pole3,pole2,-pole1)-v)<0.001:
            pole(pole3,pole2,-pole1)
        if np.abs(d(pole3,-pole2,pole1)-v)<0.001:
            pole(pole3,-pole2,pole1)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            pole(pole3,pole2,pole1)
    trace()

def undo_sym():
    global M,axes,axesh,T,V,D,Dstar,G    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alpha=np.float(ui.alpha_entry.text())
    beta=np.float(ui.beta_entry.text())
    gamma=np.float(ui.gamma_entry.text())
    alpha=alpha*np.pi/180;
    beta=beta*np.pi/180;
    gamma=gamma*np.pi/180;
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])     
    v=d(pole1,pole2,pole3)
    
    undo_pole(pole1,pole2,pole3)
    if np.abs(alpha-np.pi/2)<0.001 and np.abs(beta-np.pi/2)<0.001 and np.abs(gamma-2*np.pi/3)<0.001:
        undo_pole(pole1,pole2,pole3)
        undo_pole(pole1,pole2,-pole3)
        undo_pole(pole2,pole1,pole3)
        undo_pole(pole2,pole1,-pole3)
        undo_pole(-pole1-pole2,pole2,pole3)
        undo_pole(-pole1-pole2,pole2,-pole3)
        undo_pole(pole1,-pole1-pole2,pole3)
        undo_pole(pole1,-pole1-pole2,-pole3)
        undo_pole(pole2,-pole1-pole2,pole3)
        undo_pole(pole2,-pole1-pole2,-pole3)
        undo_pole(-pole1-pole2,pole1,pole3)
        undo_pole(-pole1-pole2,pole1,-pole3)

    else:
        if np.abs(d(pole1,pole2,-pole3)-v)<0.001:
                undo_pole(pole1,pole2,-pole3)
        if np.abs(d(pole1,-pole2,pole3)-v)<0.001:
                undo_pole(pole1,-pole2,pole3)
        if np.abs(d(-pole1,pole2,pole3)-v)<0.001:
            undo_pole(-pole1,pole2,pole3)
        if np.abs(d(pole2,pole1,pole3)-v)<0.001:
            undo_pole(pole2,pole1,pole3)
        if np.abs(d(pole2,pole1,-pole3)-v)<0.001:
            undo_pole(pole2,pole1,-pole3)
        if np.abs(d(pole2,-pole1,pole3)-v)<0.001:
            undo_pole(pole2,-pole1,pole3)
        if np.abs(d(-pole2,pole1,pole3)-v)<0.001:
            undo_pole(-pole2,pole1,pole3)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            undo_pole(pole2,pole3,pole1)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            undo_pole(pole2,pole3,-pole1)
        if np.abs(d(pole2,-pole3,pole1)-v)<0.001:
            undo_pole(pole2,-pole3,pole1)
        if np.abs(d(-pole2,pole3,pole1)-v)<0.001:
            undo_pole(-pole2,pole3,pole1)
        if np.abs(d(pole1,pole3,pole2)-v)<0.001:
            undo_pole(pole1,pole3,pole2)
        if np.abs(d(pole1,pole3,-pole2)-v)<0.001:
            undo_pole(pole1,pole3,-pole2)
        if np.abs(d(pole1,-pole3,pole2)-v)<0.001:
            undo_pole(pole1,-pole3,pole2)
        if np.abs(d(-pole1,pole3,pole2)-v)<0.001:
            undo_pole(-pole1,pole3,pole2)
        if np.abs(d(pole3,pole1,pole2)-v)<0.001:
            undo_pole(pole3,pole1,pole2)
        if np.abs(d(pole3,pole1,-pole2)-v)<0.001:
            undo_pole(pole3,pole1,-pole2)
        if np.abs(d(pole3,-pole1,pole2)-v)<0.001:
            undo_pole(pole3,-pole1,pole2)
        if np.abs(d(-pole3,pole1,pole2)-v)<0.001:
            undo_pole(-pole3,pole1,pole2)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            undo_pole(pole3,pole2,pole1)
        if np.abs(d(pole3,pole2,-pole1)-v)<0.001:
            undo_pole(pole3,pole2,-pole1)
        if np.abs(d(pole3,-pole2,pole1)-v)<0.001:
            undo_pole(pole3,-pole2,pole1)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            undo_pole(pole3,pole2,pole1)
    trace()
    
    
def addpole():
    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    pole(pole1,pole2,pole3)
    trace()
    
def undo_addpole():
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid,nn,trC
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    undo_pole(pole1,pole2,pole3)
    
    trace()
    
####################################################################
#
# Plot a given plane and equivalent ones. Plot a cone
#
####################################################################

def trace_plan(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,trP,trC
    
    pole_i=0
    pole_c=color_trace()
    
    if var_hexa()==1:
        if var_uvw()==1:
            pole1=2*np.float(ui.pole1_entry.text())+np.float(ui.pole2_entry.text())
            pole2=2*np.float(ui.pole2_entry.text())+np.float(ui.pole1_entry.text())
            pole3=np.float(ui.pole3_entry.text())
            pole_i=1
    
        
    trP=np.vstack((trP,np.array([pole1,pole2,pole3,pole_i,pole_c])))
    b=np.ascontiguousarray(trP).view(np.dtype((np.void, trP.dtype.itemsize * trP.shape[1])))
    
    trP=np.unique(b).view(trP.dtype).reshape(-1, trP.shape[1])


def trace_cone(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,trC
    
    pole_i=0
    pole_c=color_trace()
    inc=np.float(ui.inclination_entry.text())
    if var_hexa()==1:
        if var_uvw()==1:
            pole1=2*np.float(ui.pole1_entry.text())+np.float(ui.pole2_entry.text())
            pole2=2*np.float(ui.pole2_entry.text())+np.float(ui.pole1_entry.text())
            pole3=np.float(ui.pole3_entry.text())
            pole_i=1
           
    
        
    trC=np.vstack((trC,np.array([pole1,pole2,pole3,pole_i,pole_c,inc])))
    b=np.ascontiguousarray(trC).view(np.dtype((np.void, trC.dtype.itemsize * trC.shape[1])))
    
    trC=np.unique(b).view(trC.dtype).reshape(-1, trC.shape[1])

  
    
    
def trace_addplan():
    global M,axes,axesh,T,V,D,Dstar,trP
    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    
    trace_plan(pole1,pole2,pole3)
    trace_plan2
    trace()

def trace_addcone():
    global M,axes,axesh,T,V,D,Dstar,trC
    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    
    trace_cone(pole1,pole2,pole3)
    trace()
    
def undo_trace_addplan():
    global M,axes,axesh,T,V,D,Dstar,trP
    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    
    undo_trace_plan(pole1,pole2,pole3)
    trace()

def undo_trace_addcone():
    global M,axes,axesh,T,V,D,Dstar,trC
    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    
    undo_trace_cone(pole1,pole2,pole3)
    trace()
    
def undo_trace_plan(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid
    
    ind=np.where((trP[:,0]==pole1) & (trP[:,1]==pole2)& (trP[:,2]==pole3))
    indm=np.where((trP[:,0]==-pole1) & (trP[:,1]==-pole2)& (trP[:,2]==-pole3))
    
    trP=np.delete(trP,ind,0)
    trP=np.delete(trP,indm,0)
    b=np.ascontiguousarray(trP).view(np.dtype((np.void, trP.dtype.itemsize * trP.shape[1])))
    
    trP=np.unique(b).view(trP.dtype).reshape(-1, trP.shape[1])
    
def undo_trace_cone(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,trC,tr_schmid
    
    ind=np.where((trC[:,0]==pole1) & (trC[:,1]==pole2)& (trC[:,2]==pole3))
    indm=np.where((trC[:,0]==-pole1) & (trC[:,1]==-pole2)& (trC[:,2]==-pole3))
    
    trC=np.delete(trC,ind,0)
    trC=np.delete(trC,indm,0)
    b=np.ascontiguousarray(trC).view(np.dtype((np.void, trC.dtype.itemsize * trC.shape[1])))
    
    trC=np.unique(b).view(trC.dtype).reshape(-1, trC.shape[1])



def trace_plan_sym():
    global M,axes,axesh,T,V,D,Dstar,G    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alpha=np.float(ui.alpha_entry.text())
    beta=np.float(ui.beta_entry.text())
    gamma=np.float(ui.gamma_entry.text())
    alpha=alpha*np.pi/180;
    beta=beta*np.pi/180;
    gamma=gamma*np.pi/180;
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])     
    v=d(pole1,pole2,pole3)
    
    trace_plan(pole1,pole2,pole3)
    if np.abs(alpha-np.pi/2)<0.001 and np.abs(beta-np.pi/2)<0.001 and np.abs(gamma-2*np.pi/3)<0.001:
        trace_plan(pole1,pole2,pole3)
        trace_plan(pole1,pole2,-pole3)
        trace_plan(pole2,pole1,pole3)
        trace_plan(pole2,pole1,-pole3)
        trace_plan(-pole1-pole2,pole2,pole3)
        trace_plan(-pole1-pole2,pole2,-pole3)
        trace_plan(pole1,-pole1-pole2,pole3)
        trace_plan(pole1,-pole1-pole2,-pole3)
        trace_plan(pole2,-pole1-pole2,pole3)
        trace_plan(pole2,-pole1-pole2,-pole3)
        trace_plan(-pole1-pole2,pole1,pole3)
        trace_plan(-pole1-pole2,pole1,-pole3)

    else:
        if np.abs(d(pole1,pole2,-pole3)-v)<0.001:
                trace_plan(pole1,pole2,-pole3)
        if np.abs(d(pole1,-pole2,pole3)-v)<0.001:
                trace_plan(pole1,-pole2,pole3)
        if np.abs(d(-pole1,pole2,pole3)-v)<0.001:
            trace_plan(-pole1,pole2,pole3)
        if np.abs(d(pole2,pole1,pole3)-v)<0.001:
            trace_plan(pole2,pole1,pole3)
        if np.abs(d(pole2,pole1,-pole3)-v)<0.001:
            trace_plan(pole2,pole1,-pole3)
        if np.abs(d(pole2,-pole1,pole3)-v)<0.001:
            trace_plan(pole2,-pole1,pole3)
        if np.abs(d(-pole2,pole1,pole3)-v)<0.001:
            trace_plan(-pole2,pole1,pole3)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            trace_plan(pole2,pole3,pole1)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            trace_plan(pole2,pole3,-pole1)
        if np.abs(d(pole2,-pole3,pole1)-v)<0.001:
            trace_plan(pole2,-pole3,pole1)
        if np.abs(d(-pole2,pole3,pole1)-v)<0.001:
            trace_plan(-pole2,pole3,pole1)
        if np.abs(d(pole1,pole3,pole2)-v)<0.001:
            trace_plan(pole1,pole3,pole2)
        if np.abs(d(pole1,pole3,-pole2)-v)<0.001:
            trace_plan(pole1,pole3,-pole2)
        if np.abs(d(pole1,-pole3,pole2)-v)<0.001:
            trace_plan(pole1,-pole3,pole2)
        if np.abs(d(-pole1,pole3,pole2)-v)<0.001:
            trace_plan(-pole1,pole3,pole2)
        if np.abs(d(pole3,pole1,pole2)-v)<0.001:
            trace_plan(pole3,pole1,pole2)
        if np.abs(d(pole3,pole1,-pole2)-v)<0.001:
            trace_plan(pole3,pole1,-pole2)
        if np.abs(d(pole3,-pole1,pole2)-v)<0.001:
            trace_plan(pole3,-pole1,pole2)
        if np.abs(d(-pole3,pole1,pole2)-v)<0.001:
            trace_plan(-pole3,pole1,pole2)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            trace_plan(pole3,pole2,pole1)
        if np.abs(d(pole3,pole2,-pole1)-v)<0.001:
            trace_plan(pole3,pole2,-pole1)
        if np.abs(d(pole3,-pole2,pole1)-v)<0.001:
            trace_plan(pole3,-pole2,pole1)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            trace_plan(pole3,pole2,pole1)
    trace()
    
def undo_trace_plan_sym():
    global M,axes,axesh,T,V,D,Dstar,G    
    pole1=np.float(ui.pole1_entry.text())
    pole2=np.float(ui.pole2_entry.text())
    pole3=np.float(ui.pole3_entry.text())
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alpha=np.float(ui.alpha_entry.text())
    beta=np.float(ui.beta_entry.text())
    gamma=np.float(ui.gamma_entry.text())
    alpha=alpha*np.pi/180;
    beta=beta*np.pi/180;
    gamma=gamma*np.pi/180;
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])     
    v=d(pole1,pole2,pole3)
    
    undo_trace_plan(pole1,pole2,pole3)
    if np.abs(alpha-np.pi/2)<0.001 and np.abs(beta-np.pi/2)<0.001 and np.abs(gamma-2*np.pi/3)<0.001:
        undo_trace_plan(pole1,pole2,pole3)
        undo_trace_plan(pole1,pole2,-pole3)
        undo_trace_plan(pole2,pole1,pole3)
        undo_trace_plan(pole2,pole1,-pole3)
        undo_trace_plan(-pole1-pole2,pole2,pole3)
        undo_trace_plan(-pole1-pole2,pole2,-pole3)
        undo_trace_plan(pole1,-pole1-pole2,pole3)
        undo_trace_plan(pole1,-pole1-pole2,-pole3)
        undo_trace_plan(pole2,-pole1-pole2,pole3)
        undo_trace_plan(pole2,-pole1-pole2,-pole3)
        undo_trace_plan(-pole1-pole2,pole1,pole3)
        undo_trace_plan(-pole1-pole2,pole1,-pole3)

    else:
        if np.abs(d(pole1,pole2,-pole3)-v)<0.001:
                undo_trace_plan(pole1,pole2,-pole3)
        if np.abs(d(pole1,-pole2,pole3)-v)<0.001:
                undo_trace_plan(pole1,-pole2,pole3)
        if np.abs(d(-pole1,pole2,pole3)-v)<0.001:
            undo_trace_plan(-pole1,pole2,pole3)
        if np.abs(d(pole2,pole1,pole3)-v)<0.001:
            undo_trace_plan(pole2,pole1,pole3)
        if np.abs(d(pole2,pole1,-pole3)-v)<0.001:
            undo_trace_plan(pole2,pole1,-pole3)
        if np.abs(d(pole2,-pole1,pole3)-v)<0.001:
            undo_trace_plan(pole2,-pole1,pole3)
        if np.abs(d(-pole2,pole1,pole3)-v)<0.001:
            undo_trace_plan(-pole2,pole1,pole3)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            undo_trace_plan(pole2,pole3,pole1)
        if np.abs(d(pole2,pole3,pole1)-v)<0.001:
            undo_trace_plan(pole2,pole3,-pole1)
        if np.abs(d(pole2,-pole3,pole1)-v)<0.001:
            undo_trace_plan(pole2,-pole3,pole1)
        if np.abs(d(-pole2,pole3,pole1)-v)<0.001:
            undo_trace_plan(-pole2,pole3,pole1)
        if np.abs(d(pole1,pole3,pole2)-v)<0.001:
            undo_trace_plan(pole1,pole3,pole2)
        if np.abs(d(pole1,pole3,-pole2)-v)<0.001:
            undo_trace_plan(pole1,pole3,-pole2)
        if np.abs(d(pole1,-pole3,pole2)-v)<0.001:
            undo_trace_plan(pole1,-pole3,pole2)
        if np.abs(d(-pole1,pole3,pole2)-v)<0.001:
            undo_trace_plan(-pole1,pole3,pole2)
        if np.abs(d(pole3,pole1,pole2)-v)<0.001:
            undo_trace_plan(pole3,pole1,pole2)
        if np.abs(d(pole3,pole1,-pole2)-v)<0.001:
            undo_trace_plan(pole3,pole1,-pole2)
        if np.abs(d(pole3,-pole1,pole2)-v)<0.001:
            undo_trace_plan(pole3,-pole1,pole2)
        if np.abs(d(-pole3,pole1,pole2)-v)<0.001:
            undo_trace_plan(-pole3,pole1,pole2)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            undo_trace_plan(pole3,pole2,pole1)
        if np.abs(d(pole3,pole2,-pole1)-v)<0.001:
            undo_trace_plan(pole3,pole2,-pole1)
        if np.abs(d(pole3,-pole2,pole1)-v)<0.001:
            undo_trace_plan(pole3,-pole2,pole1)
        if np.abs(d(pole3,pole2,pole1)-v)<0.001:
            undo_trace_plan(pole3,pole2,pole1)
    trace()    

def trace_plan2(B):
    global M,axes,axesh,T,V,D,Dstar,a
   
    for h in range(0,B.shape[0]):
        pole1=B[h,0]
        pole2=B[h,1]
        pole3=B[h,2]
        Gs=np.array([pole1,pole2,pole3],float)
        if B[h,3]==0:                    
            Gsh=np.dot(Dstar,Gs)/np.linalg.norm(np.dot(Dstar,Gs))
        else:
            Gsh=np.dot(D,Gs)/np.linalg.norm(np.dot(D,Gs))
        S=np.dot(M,Gsh)
        
        if S[2]<0:
            S=-S
            Gsh=-Gsh
            pole1=-pole1
            pole2=-pole2
            pole3=-pole3
        r=np.sqrt(S[0]**2+S[1]**2+S[2]**2)
        A=np.zeros((2,100))
        Q=np.zeros((1,2))
        if S[2]==0:
             t=90
        else:
             t=np.arctan2(S[1],S[0])*180/np.pi
        w=0
        ph=np.arccos(S[2]/r)*180/np.pi
	
        for g in np.linspace(-np.pi,np.pi,100):
    		Aa=np.dot(Rot(t,0,0,1),np.dot(Rot(ph,0,1,0),np.array([np.sin(g),np.cos(g),0])))
    		A[:,w]=proj(Aa[0],Aa[1],Aa[2])*600/2
    		Q=np.vstack((Q,A[:,w]))
    		w=w+1
        
        Q=np.delete(Q,0,0)   
	if B[h,4]==1:
		a.plot(Q[:,0]+600/2,Q[:,1]+600/2,'g')
	if B[h,4]==2:
		a.plot(Q[:,0]+600/2,Q[:,1]+600/2,'b')
	if B[h,4]==3:
		a.plot(Q[:,0]+600/2,Q[:,1]+600/2,'r')
       
def trace_cone2(B):
    global M,axes,axesh,T,V,D,Dstar,a
   
    for h in range(0,B.shape[0]):
        pole1=B[h,0]
        pole2=B[h,1]
        pole3=B[h,2]
        i=B[h,5]
        Gs=np.array([pole1,pole2,pole3],float)
        if B[h,3]==0:                    
            Gsh=np.dot(Dstar,Gs)/np.linalg.norm(np.dot(Dstar,Gs))
        else:
            Gsh=np.dot(D,Gs)/np.linalg.norm(np.dot(D,Gs))
        S=np.dot(M,Gsh)
        
        if S[2]<0:
            S=-S
            Gsh=-Gsh
            pole1=-pole1
            pole2=-pole2
            pole3=-pole3
        r=np.sqrt(S[0]**2+S[1]**2+S[2]**2)
        A=np.zeros((3,100))
        Q=np.zeros((1,3))
        if S[2]==0:
             t=90
        else:
             t=np.arctan2(S[1],S[0])*180/np.pi
        w=0
        ph=np.arccos(S[2]/r)*180/np.pi
	

        for g in np.linspace(-np.pi,np.pi,100):
    		Aa=np.dot(Rot(t,0,0,1),np.dot(Rot(ph,0,1,0),np.array([np.sin(g)*np.sin(i*np.pi/180),np.cos(g)*np.sin(i*np.pi/180),np.cos(i*np.pi/180)])))
    		A[:,w]=proj2(Aa[0],Aa[1],Aa[2])*600/2
    		Q=np.vstack((Q,A[:,w]))
    		w=w+1
        
        Q=np.delete(Q,0,0)   
        
        asign = np.sign(Q[:,2])
	signchange = ((np.roll(asign, 1) - asign) != 0).astype(int)
	wp=np.where(signchange==1)[0]
        wp=np.append(0,wp)
        wp=np.append(wp,99)

	for tt in range(0, np.shape(wp)[0]-1):       
		if B[h,4]==1:
			a.plot(Q[int(wp[tt]):int(wp[tt+1]),0]+600/2,Q[int(wp[tt]):int(wp[tt+1]),1]+600/2,'g')
		if B[h,4]==2:
			a.plot(Q[int(wp[tt]):int(wp[tt+1]),0]+600/2,Q[int(wp[tt]):int(wp[tt+1]),1]+600/2,'b')
		if B[h,4]==3:
			a.plot(Q[int(wp[tt]):int(wp[tt+1]),0]+600/2,Q[int(wp[tt]):int(wp[tt+1]),1]+600/2,'r')
            
            
        
####################################################################
#
# Click a pole 
#
####################################################################    

def click_a_pole(event):
        
    global M,Dstar,D,minx,maxx,miny,maxy,a
      
    if event.button==3:
            x=event.xdata
            y=event.ydata
             
            x=(x-300)/300
            y=(y-300)/300
            X=2*x/(1+x**2+y**2)
            Y=2*y/(1+x**2+y**2)
            Z=(-1+x**2+y**2)/(1+x**2+y**2)
            if Z<0:
                X=-X
                Y=-Y
            A=np.dot(np.linalg.inv(M),np.array([X,Y,Z]))
            n=0
            L=np.zeros((3,16**3))                      
                                 
            for i in range(-8,9,1):
                for j in range(-8,9,1):
                    for k in range(-8,9,1):
                        if np.linalg.norm([i,j,k])<>0:
                            if var_uvw()==0:
                                Q=np.dot(Dstar,np.array([i,j,k],float))/np.linalg.norm(np.dot(Dstar,np.array([i,j,k],float)))
                                if np.abs(Q[0]-A[0])<0.05 and np.abs(Q[1]-A[1])<0.05 and np.abs(Q[2]-A[2])<0.05:
                                    L[:,n]=np.array([i,j,k],float)
                                    n=n+1
                                   
                            else:
                                  
                                Q=np.dot(D,np.array([i,j,k],float))/np.linalg.norm(np.dot(D,np.array([i,j,k],float)))
                                if np.abs(Q[0]-A[0])<0.05 and np.abs(Q[1]-A[1])<0.05 and np.abs(Q[2]-A[2])<0.05:
                                    L[:,n]=np.array([i,j,k],float)
                                    n=n+1
              
        
            if np.linalg.norm(L[:,0])<>0:
                if var_hexa()==1:
                    if var_uvw()==1:
                        La=(2*L[0,0]-L[1,0])/3
                        Lb=(2*L[1,0]-L[0,0])/3
                        L[0,0]=La
                        L[1,0]=Lb

                pole(L[0,0],L[1,0],L[2,0])
                trace()

####################################################################
#
# Inclinaison-beta indicator when the mouse is on the stereo
#
#################################################################### 
  
def coordinates(event):

    if event.xdata and event.ydata:
	    x=event.xdata
	    y=event.ydata    
	    x=(x-300)/300
	    y=(y-300)/300
	    long0=90*np.pi/180
	    lat0=0
	    r=np.sqrt(x**2+y**2)
	    c=2*np.arctan(r)
	    longi=(long0+np.arctan2(x*np.sin(c),r*np.cos(lat0)*np.cos(c)-y*np.sin(lat0)*np.sin(c)))*180/np.pi 
	    lat=np.arcsin(np.cos(c)*np.sin(lat0)+y*np.sin(c)*np.cos(lat0)/r)*180/np.pi
	    lat=90+lat
	    longi=-longi+180
	    if longi>90:
	     longi=longi-180
	    c=str(np.around(longi,decimals=1))+str(',')+str(np.around(lat,decimals=1))
	    ui.coord_label.setText(str(c))

########################################################
#
# Calculate interplanar distance 
#
#######################################################

def dhkl():
    i=np.float(ui.pole1_entry.text())
    j=np.float(ui.pole2_entry.text())
    k=np.float(ui.pole3_entry.text())
    a=np.float(ui.a_entry.text())
    b=np.float(ui.b_entry.text())
    c=np.float(ui.c_entry.text())
    alp=np.float(ui.alpha_entry.text())
    bet=np.float(ui.beta_entry.text())
    gam=np.float(ui.gamma_entry.text())
    alp=alp*np.pi/180;
    bet=bet*np.pi/180;
    gam=gam*np.pi/180;
    G=np.array([[a**2,a*b*np.cos(gam),a*c*np.cos(bet)],[a*b*np.cos(gam),b**2,b*c*np.cos(alp)],[a*c*np.cos(bet),b*c*np.cos(alp),c**2]])    
    d=np.around(1/(np.sqrt(np.dot(np.array([i,j,k]),np.dot(np.linalg.inv(G),np.array([i,j,k]))))), decimals=3)
    ui.dhkl_label.setText(str(d))
    return        

####################################################################
#
# Reset view after zoom
#
#################################################################### 

def reset_view():
	global a
	
	a.axis([minx,maxx,miny,maxy])
	trace()
	
####################################################################
#
# Enable or disable Wulff net
#
#################################################################### 

def wulff():
	global a
	if ui.wulff_button.isChecked():
		fn = os.path.join(os.path.dirname(__file__), 'stereo.png')      
		img=Image.open(fn)
		img= np.array(img)
	else:
		img = 255*np.ones([600,600,3],dtype=np.uint8)
		circle = plt.Circle((300, 300), 300, color='black',fill=False)
		a.add_artist(circle)
		a.plot(300,300,'+',markersize=10,mew=3,color='black')
	
	a.imshow(img,interpolation="bicubic")
	a.axis('off')
    	a.figure.canvas.draw()  
	


 #######################################################################               
#######################################################################
#
# Main
#
#####################################################################    


####################################################################
#
# Refresh action on stereo
#
####################################################################

def trace():
    global T,x,y,z,axes,axesh,M,trP,a,trC
    minx,maxx=a.get_xlim()
    miny,maxy=a.get_ylim()
    a = figure.add_subplot(111) 
    a.figure.clear()
    a = figure.add_subplot(111)
    P=np.zeros((axes.shape[0],2))
    T=np.zeros((axes.shape))
    C=[]
    
    trace_plan2(trP)
    trace_cone2(trC)			
    schmid_trace2(tr_schmid)
    
    for i in range(0,axes.shape[0]):
        axeshr=np.array([axesh[i,0],axesh[i,1],axesh[i,2]])

        axeshr=axeshr/np.linalg.norm(axeshr)
        if axesh[i,4]==1:
            C.append('g')
        if axesh[i,4]==2:
            C.append('b')
        if axesh[i,4]==3:
            C.append('r')

               
        T[i,:]=np.dot(M,axeshr)
        P[i,:]=proj(T[i,0],T[i,1],T[i,2])*600/2
        m=np.amax([np.abs(axes[i,0]),np.abs(axes[i,1]),np.abs(axes[i,2])])
        if (np.around(axes[i,0]/m)==axes[i,0]/m) & (np.around(axes[i,1]/m)==axes[i,1]/m) & (np.around(axes[i,2]/m)==axes[i,2]/m):
            if var_hexa()==0:
                s=str(int(axes[i,0]/m))+str(int(axes[i,1]/m))+str(int(axes[i,2]/m))
            if var_hexa()==1:
                if axesh[i,3]==0:
                    s='('+str(int(axes[i,0]/m))+str(int(axes[i,1]/m))+str(-int(axes[i,1]/m)-int(axes[i,0]/m))+str(int(axes[i,2]/m))+')'
                if axesh[i,3]==1:
                    s='['+str(int(2*(axes[i,0]/m)-axes[i,1]/m))+str(int(2*(axes[i,1]/m)-axes[i,0]/m))+str(-int(axes[i,1]/m)-int(axes[i,0]/m))+str(int(3*axes[i,2]/m))+']'
                
        else:
            if var_hexa()==0:
                s=str(int(axes[i,0]))+str(int(axes[i,1]))+str(int(axes[i,2]))
            if var_hexa()==1:
                if axesh[i,3]==0:
                    s='('+str(int(axes[i,0]))+str(int(axes[i,1]))+str(-int(axes[i,1])-int(axes[i,0]))+str(int(axes[i,2]))+')'
                if axesh[i,3]==1:
                    s='['+str(int(2*(axes[i,0])-axes[i,1]))+str(int(2*(axes[i,1])-axes[i,0]))+str(-int(axes[i,1])-int(axes[i,0]))+str(int(3*axes[i,2]))+']'
             
            
        a.annotate(s,(P[i,0]+600/2,P[i,1]+600/2))
       
    if var_carre()==0:           
        a.scatter(P[:,0]+600/2,P[:,1]+600/2,c=C,s=np.float(ui.size_var.text()))
    else:
        a.scatter(P[:,0]+600/2,P[:,1]+600/2,edgecolor=C, s=np.float(ui.size_var.text()), facecolors='none', linewidths=1.5)       
    
    a.axis([minx,maxx,miny,maxy])
    wulff()
    
 ####################################
 #
 # Initial plot from a given diffraction
 #
 ####################################
 
def princ():
    global T,angle_alpha, angle_beta, angle_z,M,Dstar,D,g,M0,trP,axeshr,nn,a,minx,maxx,miny,maxy,trC
    trP=np.zeros((1,5))
    trC=np.zeros((1,6))
    crist() 
    a = figure.add_subplot(111)
    a.figure.clear()
    a = figure.add_subplot(111)
    
    
    diff1=np.float(ui.diff1_entry.text())
    diff2=np.float(ui.diff2_entry.text())
    diff3=np.float(ui.diff3_entry.text())
    tilt=np.float(ui.tilt_entry.text())
    inclinaison=np.float(ui.inclinaison_entry.text())    
     
    d0=np.array([diff1,diff2,diff3])
    if var_uvw()==0: 
       d=np.dot(Dstar,d0)
              
    else:
       d=np.dot(Dstar,d0)
    if diff2==0 and diff1==0:
        normal=np.array([1,0,0])
        ang=np.pi/2
    else:
        normal=np.array([-d[2],0,d[0]])
        ang=np.arccos(np.dot(d,np.array([0,1,0]))/np.linalg.norm(d))
    
    R=np.dot(Rot(-tilt,0,1,0),np.dot(Rot(-inclinaison,0,0,1),Rot(ang*180/np.pi, normal[0],normal[1],normal[2])))    
       
    P=np.zeros((axes.shape[0],2))
    T=np.zeros((axes.shape))
    nn=axes.shape[0]
    C=[]
    for i in range(0,axes.shape[0]):
        
        axeshr=np.array([axesh[i,0],axesh[i,1],axesh[i,2]])
        axeshr=axeshr/np.linalg.norm(axeshr)
        T[i,:]=np.dot(R,axeshr)
        P[i,:]=proj(T[i,0],T[i,1],T[i,2])*600/2
        if color_trace()==1:
            C.append('g')
            axesh[i,4]=1
        if color_trace()==2:
            C.append('b')
            axesh[i,4]=2
        if color_trace()==3:
            C.append('r')
            axesh[i,4]=3
        m=np.amax([np.abs(axes[i,0]),np.abs(axes[i,1]),np.abs(axes[i,2])])
        if (np.around(axes[i,0]/m)==axes[i,0]/m) & (np.around(axes[i,1]/m)==axes[i,1]/m) & (np.around(axes[i,2]/m)==axes[i,2]/m):
            if var_hexa()==0:
                s=str(int(axes[i,0]/m))+str(int(axes[i,1]/m))+str(int(axes[i,2]/m))
            if var_hexa()==1:
                if axesh[i,3]==0:
                    s='('+str(int(axes[i,0]/m))+str(int(axes[i,1]/m))+str(-int(axes[i,1]/m)-int(axes[i,0]/m))+str(int(axes[i,2]/m))+')'
                if axesh[i,3]==1:
                    s='['+str(int(2*(axes[i,0]/m)-axes[i,1]/m))+str(int(2*(axes[i,1]/m)-axes[i,0]/m))+str(-int(axes[i,1]/m)-int(axes[i,0]/m))+str(int(3*axes[i,2]/m))+']'
                
        else:
            if var_hexa()==0:
                s=str(int(axes[i,0]))+str(int(axes[i,1]))+str(int(axes[i,2]))
            if var_hexa()==1:
                if axesh[i,3]==0:
                    s='('+str(int(axes[i,0]))+str(int(axes[i,1]))+str(-int(axes[i,1])-int(axes[i,0]))+str(int(axes[i,2]))+')'
                if axesh[i,3]==1:
                    s='['+str(int(2*(axes[i,0])-axes[i,1]))+str(int(2*(axes[i,1])-axes[i,0]))+str(-int(axes[i,1])-int(axes[i,0]))+str(int(3*axes[i,2]))+']'
                
             
        a.annotate(s,(P[i,0]+600/2,P[i,1]+600/2))
        
    if var_carre()==0:           
        a.scatter(P[:,0]+600/2,P[:,1]+600/2,c=C,s=np.float(ui.size_var.text()))
    else:
        a.scatter(P[:,0]+600/2,P[:,1]+600/2,edgecolor=C, s=np.float(ui.size_var.text()), facecolors='none', linewidths=1.5)            
    
    minx,maxx=-2,602
    miny,maxy=-2,602
    a.axis([minx,maxx,miny,maxy])
    wulff()
    
    angle_alpha=0             
    angle_beta=0
    angle_z=0
    g=0
    ui.angle_alpha_label_2.setText('0.0')
    ui.angle_beta_label_2.setText('0.0')
    ui.angle_z_label_2.setText('0.0')
    ui.angle_beta_label_2.setText('0.0')
    ui.angle_z_label_2.setText('0.0')    
    ui.rg_label.setText('0.0')
    M=R
    M0=R
    phir=np.arccos(M[2,2])*180/np.pi
    phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
    phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
    t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
    
    ui.angle_euler_label.setText(t)
    return T,angle_alpha,angle_beta,angle_z,g,M,M0
    
##############################################"
#
# Plot from Euler angle
#
##################################################"

def princ2():
    global T,angle_alpha,angle_beta,angle_z,M,Dstar,D,g,M0,trP,a,axeshr,nn,minx,maxx,miny,maxy,trC
    
    trP=np.zeros((1,5))
    trC=np.zeros((1,6))
    a = figure.add_subplot(111)
    a.figure.clear()
    a = figure.add_subplot(111)
    phi1=np.float(ui.phi1_entry.text())
    phi=np.float(ui.phi_entry.text())
    phi2=np.float(ui.phi2_entry.text())
    fn = os.path.join(os.path.dirname(__file__), 'stereo.png')      
    img=np.array(Image.open(fn))
    crist()    
    P=np.zeros((axes.shape[0],2))
    T=np.zeros((axes.shape))
    nn=axes.shape[0]
    C=[]    
    
    for i in range(0,axes.shape[0]):
        axeshr=np.array([axesh[i,0],axesh[i,1],axesh[i,2]])
        axeshr=axeshr/np.linalg.norm(axeshr)
        T[i,:]=np.dot(rotation(phi1,phi,phi2),axeshr)
        
        P[i,:]=proj(T[i,0],T[i,1],T[i,2])*600/2
        if color_trace()==1:
            C.append('g')
            axesh[i,4]=1
        if color_trace()==2:
            C.append('b')
            axesh[i,4]=2
        if color_trace()==3:
            C.append('r')
            axesh[i,4]=3

        m=np.amax([np.abs(axes[i,0]),np.abs(axes[i,1]),np.abs(axes[i,2])])
        if (np.around(axes[i,0]/m)==axes[i,0]/m) & (np.around(axes[i,1]/m)==axes[i,1]/m) & (np.around(axes[i,2]/m)==axes[i,2]/m):
            if var_hexa()==0:
                s=str(int(axes[i,0]/m))+str(int(axes[i,1]/m))+str(int(axes[i,2]/m))
            if var_hexa()==1:
                if axesh[i,3]==0:
                    s='('+str(int(axes[i,0]/m))+str(int(axes[i,1]/m))+str(-int(axes[i,1]/m)-int(axes[i,0]/m))+str(int(axes[i,2]/m))+')'
                if axesh[i,3]==1:
                    s='['+str(int(2*(axes[i,0]/m)-axes[i,1]/m))+str(int(2*(axes[i,1]/m)-axes[i,0]/m))+str(-int(axes[i,1]/m)-int(axes[i,0]/m))+str(int(3*axes[i,2]/m))+']'
                
        else:
            if var_hexa()==0:
                s=str(int(axes[i,0]))+str(int(axes[i,1]))+str(int(axes[i,2]))
            if var_hexa()==1:
                if axesh[i,3]==0:
                    s='('+str(int(axes[i,0]))+str(int(axes[i,1]))+str(-int(axes[i,1])-int(axes[i,0]))+str(int(axes[i,2]))+')'
                if axesh[i,3]==1:
                    s='['+str(int(2*(axes[i,0])-axes[i,1]))+str(int(2*(axes[i,1])-axes[i,0]))+str(-int(axes[i,1])-int(axes[i,0]))+str(int(3*axes[i,2]))+']'
              
        a.annotate(s,(P[i,0]+600/2,P[i,1]+600/2))
        
    if var_carre()==0:           
        a.scatter(P[:,0]+600/2,P[:,1]+600/2,c=C,s=np.float(ui.size_var.text()))
    else:
        a.scatter(P[:,0]+600/2,P[:,1]+600/2,edgecolor=C, s=np.float(ui.size_var.text()), facecolors='none', linewidths=1.5)       
    minx,maxx=-2,602
    miny,maxy=-2,602
    a.axis([minx,maxx,miny,maxy])
    wulff()
    
    angle_alpha=0             
    angle_beta=0
    angle_z=0
    g=0
    ui.angle_alpha_label_2.setText('0.0')
    ui.angle_beta_label_2.setText('0.0')
    ui.angle_z_label_2.setText('0.0')
    ui.angle_beta_label_2.setText('0.0')
    ui.angle_z_label_2.setText('0.0')    
    ui.rg_label.setText('0.0')
    M=rotation(phi1,phi,phi2)
    t=str(np.around(phi1,decimals=1))+str(',')+str(np.around(phi,decimals=1))+str(',')+str(np.around(phi2,decimals=1))
    ui.angle_euler_label.setText(t)
    
    return T,angle_alpha,angle_beta,angle_z,g,M

  
  
#######################################################################
#######################################################################
#
# GUI Menu/Dialog 
#
#######################################################################


######################################################
#
# Menu
#
##########################################################

###########################################################
#
# Structure
#
##############################################################

def structure(item):
    global x0, var_hexa, d_label_var, e_entry
    
    ui.a_entry.setText(str(item[1]))
    ui.b_entry.setText(str(item[2]))
    ui.c_entry.setText(str(item[3]))
    ui.alpha_entry.setText(str(item[4]))
    ui.beta_entry.setText(str(item[5]))
    ui.gamma_entry.setText(str(item[6]))
    if eval(item[4])==90 and eval(item[5])==90 and eval(item[6])==120 :
        ui.hexa_button.setChecked(True)
        ui.e_entry.setText('2')
        ui.d_label_var.setText('3')
    else:
        ui.d_entry.setText('1')
        ui.e_entry.setText('1')
    
 

####################################################################
#
# Measuring angle between two poles (for the angle dialog box)
#
####################################################################


        
def angle():
	global Dstar
	c100=np.float(ui_angle.n10.text())
	c110=np.float(ui_angle.n11.text())
	c120=np.float(ui_angle.n12.text())
	c200=np.float(ui_angle.n20.text())
	c210=np.float(ui_angle.n21.text())
	c220=np.float(ui_angle.n22.text())
	c1=np.array([c100,c110,c120])
	c2=np.array([c200,c210,c220])
	if ui.uvw_button.isChecked==True: 
	   c1c=np.dot(Dstar,c1)
	   c2c=np.dot(Dstar,c2)
	else:
	   c1c=np.dot(Dstar,c1)
	   c2c=np.dot(Dstar,c2)
	the=np.arccos(np.dot(c1c,c2c)/(np.linalg.norm(c1c)*np.linalg.norm(c2c)))                   
	thes=str(np.around(the*180/np.pi,decimals=2))        
	ui_angle.angle_label.setText(thes)

                        

 
##################################################
#
# Schmid factor calculation (for the Schmid dialog box). Calculate the Schmid factor for a 
# given b,n couple or for equivalent couples
#
################################################### 
def prod_scal(c1,c2):
    global M, Dstar, D
    alp=np.float(ui.alpha_entry.text())
    bet=np.float(ui.beta_entry.text())
    gam=np.float(ui.gamma_entry.text())
    alp=alp*np.pi/180;
    bet=bet*np.pi/180;
    gam=gam*np.pi/180;
    if np.abs(alp-np.pi/2)<0.001 and np.abs(bet-np.pi/2)<0.001 and np.abs(gam-2*np.pi/3)<0.001:
        c2p=np.array([0,0,0])        
        c2p[0]=2*c2[0]+c2[1]
        c2p[1]=2*c2[1]+c2[0]
        c2p[2]=c2[2]
        c2c=np.dot(D, c2p)
    else:
        c2c=np.dot(D, c2)
    
    c1c=np.dot(Dstar,c1)
    p=np.dot(c1c,c2c)
    return p
    
def schmid_calc(b,n, T):
    global D, Dstar,M
    alp=np.float(ui.alpha_entry.text())
    bet=np.float(ui.beta_entry.text())
    gam=np.float(ui.gamma_entry.text())
    alp=alp*np.pi/180;
    bet=bet*np.pi/180;
    gam=gam*np.pi/180;
    if np.abs(alp-np.pi/2)<0.001 and np.abs(bet-np.pi/2)<0.001 and np.abs(gam-2*np.pi/3)<0.001:
        b2=np.array([0,0,0])        
        b2[0]=2*b[0]+b[1]
        b2[1]=2*b[1]+b[0]
        b2[2]=b[2]
        bpr=np.dot(D, b2)
    else:
        bpr=np.dot(D, b)
     
    npr=np.dot(Dstar,n)
    npr2=np.dot(M,npr)
    bpr2=np.dot(M,bpr)
    T=T/np.linalg.norm(T)
    anglen=np.arccos(np.dot(npr2,T)/np.linalg.norm(npr2))
    angleb=np.arccos(np.dot(bpr2,T)/np.linalg.norm(bpr2))
    s=np.cos(anglen)*np.cos(angleb)

    return s

def schmid_pole(pole1,pole2,pole3):
	global M,V,D,Dstar,G
	alp=np.float(ui.alpha_entry.text())
        bet=np.float(ui.beta_entry.text())
        gam=np.float(ui.gamma_entry.text())
        alp=alp*np.pi/180;
	bet=bet*np.pi/180;
	gam=gam*np.pi/180;
	v=d(pole1,pole2,pole3)
	N=np.array([pole1,pole2,pole3])
	if np.abs(alp-np.pi/2)<0.001 and np.abs(bet-np.pi/2)<0.001 and np.abs(gam-2*np.pi/3)<0.001:
		N=np.array([[pole1,pole2,pole3],[pole1,pole2,-pole3],[pole2,pole1,pole3],[pole2,pole1,-pole3],[-pole1-pole2,pole2,pole3],[-pole1-pole2,pole2,-pole3],[pole1,-pole1-pole2,pole3],[pole1,-pole1-pole2,-pole3],[pole2,-pole1-pole2,pole3],[pole2,-pole1-pole2,-pole3],[-pole1-pole2,pole1,pole3],[-pole1-pole2,pole1,-pole3]])
	else:	
        	if np.abs(d(pole1,pole2,-pole3)-v)<0.001:
                    N=np.vstack((N,np.array([pole1,pole2,-pole3])))
        	if np.abs(d(pole1,-pole2,pole3)-v)<0.001:
        			N=np.vstack((N,np.array([pole1,-pole2,pole3])))
        	if np.abs(d(-pole1,pole2,pole3)-v)<0.001:
        			N=np.vstack((N,np.array([-pole1,pole2,pole3])))
        	if np.abs(d(pole2,pole1,pole3)-v)<0.001:
        			N=np.vstack((N,np.array([pole2,pole1,pole3])))
        	if np.abs(d(pole2,pole1,-pole3)-v)<0.001:
        		N=np.vstack((N,np.array([pole2,pole1,-pole3])))
        	if np.abs(d(pole2,-pole1,pole3)-v)<0.001:
        		N=np.vstack((N,np.array([pole2,-pole1,pole3])))
        	if np.abs(d(-pole2,pole1,pole3)-v)<0.001:
        		N=np.vstack((N,np.array([-pole2,pole1,pole3])))
        	if np.abs(d(pole2,pole3,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole2,pole3,pole1])))
        	if np.abs(d(pole2,pole3,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole2,pole3,-pole1])))
        	if np.abs(d(pole2,-pole3,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole2,-pole3,pole1])))
        	if np.abs(d(-pole2,pole3,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([-pole2,pole3,pole1])))
        	if np.abs(d(pole1,pole3,pole2)-v)<0.001:
        		N=np.vstack((N,np.array([pole1,pole3,pole2])))
        	if np.abs(d(pole1,pole3,-pole2)-v)<0.001:
        		N=np.vstack((N,np.array([pole1,pole3,-pole2])))
        	if np.abs(d(pole1,-pole3,pole2)-v)<0.001:
        		N=np.vstack((N,np.array([pole1,-pole3,pole2])))
        	if np.abs(d(-pole1,pole3,pole2)-v)<0.001:
        		N=np.vstack((N,np.array([-pole1,pole3,pole2])))
        	if np.abs(d(pole3,pole1,pole2)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,pole1,pole2])))
        	if np.abs(d(pole3,pole1,-pole2)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,pole1,-pole2])))
        	if np.abs(d(pole3,-pole1,pole2)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,-pole1,pole2])))
        	if np.abs(d(-pole3,pole1,pole2)-v)<0.001:
        		N=np.vstack((N,np.array([-pole3,pole1,pole2])))
        	if np.abs(d(pole3,pole2,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,pole2,pole1])))
        	if np.abs(d(pole3,pole2,-pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,pole2,-pole1])))
        	if np.abs(d(pole3,-pole2,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,-pole2,pole1])))
        	if np.abs(d(pole3,pole2,pole1)-v)<0.001:
        		N=np.vstack((N,np.array([pole3,pole2,pole1])))
	
		  
	return N


        
def schmid():
	global D, Dstar,M
	h=np.float(ui_schmid.n0.text())
	k=np.float(ui_schmid.n1.text())
	l=np.float(ui_schmid.n2.text())
	u=np.float(ui_schmid.b0.text())
	v=np.float(ui_schmid.b1.text())
	w=np.float(ui_schmid.b2.text())
	n=np.array([h,k,l])
	b=np.array([u,v,w])
	T=np.array([np.float(ui_schmid.T0.text()),np.float(ui_schmid.T1.text()),np.float(ui_schmid.T2.text())])
	s=schmid_calc(b,n,T)
	ui_schmid.schmid_factor_label.setText(str(np.around(s,decimals=2)))
	B=schmid_pole(u,v,w)
        N=schmid_pole(h,k,l)
        P=np.array([0,0,0,0,0,0,0])
	for i in range(0,np.shape(N)[0]):
		for j in range(0,np.shape(B)[0]):
                   if np.abs(prod_scal(N[i,:],B[j,:]))<0.0001:
                      s=schmid_calc(B[j,:],N[i,:],T)
                      R=np.array([s,N[i,0],N[i,1],N[i,2],B[j,0],B[j,1],B[j,2]])
                      P=np.vstack((P,R))
                     
        P=np.delete(P, (0), axis=0)
        P=unique_rows(P)
        P=-P
        P.view('float64,i8,i8,i8,i8,i8,i8').sort(order=['f0'], axis=0)
        P=-P
        ui_schmid.schmid_text.setText( 's | n | b')
        for k in range(0,np.shape(P)[0]):                                   
           ui_schmid.schmid_text.append(str(np.around(P[k,0],decimals=3))+ '| '+str(np.int(P[k,1]))+ str(np.int(P[k,2])) +str(np.int(P[k,3]))+ '| '+ str(np.int(P[k,4]))+str(np.int(P[k,5]))+str(np.int(P[k,6])))
        

                        
 #######################################
 #
 # Save stereo as png
 #
 ############################################"

def image_save():
    filename=QtGui.QFileDialog.getSaveFileName( Index,"Save file", "", ".png")
    pixmap = QtGui.QPixmap.grabWidget(canvas,55,49,710,710)
    pixmap.save(str(filename)+".png")
     
     
##################################################
#
# Calculating x,y,z direction (for xyz dialog box)
#
################################################### 

   
def center():
	global D, Dstar,M
	A=np.dot(np.linalg.inv(M),np.array([0,0,1]))
	A2=np.dot(np.linalg.inv(M),np.array([1,0,0]))
	A3=np.dot(np.linalg.inv(M),np.array([0,1,0]))
	C=np.dot(np.linalg.inv(Dstar),A)
	Zp=C/np.linalg.norm(C)
	C2=np.dot(np.linalg.inv(Dstar),A2)
	Xp=C2/np.linalg.norm(C2)
	C3=np.dot(np.linalg.inv(Dstar),A3)
	Yp=C3/np.linalg.norm(C3)    
	
	ui_xyz.X_text.setText(str(Xp[0]*100)+', '+str(Xp[1]*100)+', '+str(Xp[2]*100))
	ui_xyz.Y_text.setText(str(Yp[0]*100)+', '+str(Yp[1]*100)+', '+str(Yp[2]*100))
	ui_xyz.Z_text.setText(str(Zp[0]*100)+', '+str(Zp[1]*100)+', '+str(Zp[2]*100))
 

 
##########################################################################
#
#  Apparent width class for dialog box: plot the width of a plane of given normal hkl with the tilt alpha angle. Plot trace direction with respect to the tilt axis
#
##########################################################################

 
def plot_width():
	global D, Dstar, M
	ui_width.figure.clf()
	B=np.dot(np.linalg.inv(M),np.array([0,0,1]))
	
	plan1=np.float(ui_width.n0.text())   
	plan2=np.float(ui_width.n1.text())
	plan3=np.float(ui_width.n2.text())
	n=np.array([plan1,plan2,plan3])
	n2=np.dot(Dstar,n)
	n2=n2/np.linalg.norm(n2)
	B=np.dot(Dstar,B)
	B=B/np.linalg.norm(B)
	nr=np.dot(M,n2)
	la=np.zeros((1,41))
	la2=np.zeros((2,41))
	k=0
	T=np.cross(nr,B)
	T=T/np.linalg.norm(T)

		
	for t in range(-40,41,2):
	    Mi=np.dot(Rot(t,0,1,0),M)
	    Bi=np.dot(np.linalg.inv(Mi),np.array([0,0,1]))
	    Bi=np.dot(Dstar,Bi)
	    Bi=Bi/np.linalg.norm(Bi)
	    Ti=np.dot(Rot(t,0,1,0),T)
	    
	    la[0,k]=np.dot(nr,Bi)
	    la2[1,k]=np.arctan(Ti[0]/Ti[1])*180/np.pi
	    la2[0,k]=np.dot(nr,Bi)/np.sqrt(1-np.dot(T,Bi)**2)

	    k=k+1

	ax1 = ui_width.figure.add_subplot(111)
	ax1.set_xlabel('alpha tilt angle')

	ax1.set_ylabel('w/w(0)', color='black')
	ax1.tick_params('y', colors='black')
	if ui_width.trace_radio_button.isChecked():
		ax2 = ax1.twinx()
		ax2.plot(range(-40,41,2),la2[1,:],'b-')
		ax2.set_ylabel('trace angle', color='b')
		ax2.tick_params('y', colors='b')
	ax1.plot(range(-40,41,2),la2[0,:],'r-')
	
	ui_width.canvas.draw_idle()
	
	



##################################################
#
# Add matplotlib toolbar to zoom and pan
#
################################################### 


class NavigationToolbar(NavigationToolbar):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Pan', 'Zoom')]
    def set_message(self, msg):
        pass


#############################################################
#
# Launch
#
#############################################################"
    
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)
    
if __name__ == "__main__":
    
	app = QtGui.QApplication(sys.argv)
	Index = QtGui.QMainWindow()	
	ui = stereoprojUI.Ui_StereoProj()
	ui.setupUi(Index)
	figure=plt.figure()
	canvas=FigureCanvas(figure)
	ui.mplvl.addWidget(canvas)
	toolbar = NavigationToolbar(canvas, canvas)
	toolbar.setMinimumWidth(601)

# Read structure file
	
	file_struct=open(os.path.join(os.path.dirname(__file__), 'structure.txt') ,"r")
	x0=[]
	for line in file_struct:
	    x0.append(map(str, line.split()))
	i=0
	file_struct.close()            
	for item in x0:
	    entry = ui.menuStructure.addAction(item[0])
	    Index.connect(entry,QtCore.SIGNAL('triggered()'), lambda item=item: structure(item))
	    i=i+1

# Connect dialog boxes and buttons

	Index.connect(ui.actionSave_figure, QtCore.SIGNAL('triggered()'), image_save) 

	Angle=QtGui.QDialog()
	ui_angle=angleUI.Ui_Angle()
	ui_angle.setupUi(Angle)
	Index.connect(ui.actionCalculate_angle, QtCore.SIGNAL('triggered()'), Angle.show) 
	ui_angle.buttonBox.rejected.connect(Angle.close)
	ui_angle.buttonBox.accepted.connect(angle)

	Xyz=QtGui.QDialog()
	ui_xyz=xyzUI.Ui_xyz_dialog()
	ui_xyz.setupUi(Xyz)
	Index.connect(ui.actionCalculate_xyz, QtCore.SIGNAL('triggered()'), Xyz.show)
	ui_xyz.xyz_button.clicked.connect(center)
	
	Schmid=QtGui.QDialog()
	ui_schmid=schmidUI.Ui_Schmid()
	ui_schmid.setupUi(Schmid)
	Index.connect(ui.actionCalculate_Schmid_factor, QtCore.SIGNAL('triggered()'), Schmid.show) 
	ui_schmid.buttonBox.rejected.connect(Schmid.close)
	ui_schmid.buttonBox.accepted.connect(schmid)

	Width=QtGui.QDialog()
	ui_width=widthUI.Ui_Width()
	ui_width.setupUi(Width)
	Index.connect(ui.actionCalculate_apparent_width, QtCore.SIGNAL('triggered()'), Width.show) 
	ui_width.buttonBox.rejected.connect(Width.close)
	ui_width.buttonBox.accepted.connect(plot_width)
	
	Intersections = QtGui.QDialog()
	ui_inter=intersectionsUI.Ui_Intersections()
	ui_inter.setupUi(Intersections)
	Index.connect(ui.actionCalculate_intersections, QtCore.SIGNAL('triggered()'), Intersections.show) 
	def center():
	    print 'a'  
	ui_inter.pushButton_3.clicked.connect(center)            
	
	
	ui.button_trace2.clicked.connect(princ2)
	ui.button_trace.clicked.connect(princ)
	ui.angle_alpha_buttonp.clicked.connect(rot_alpha_p)
	ui.angle_alpha_buttonm.clicked.connect(rot_alpha_m)
	ui.angle_beta_buttonp.clicked.connect(rot_beta_p)
	ui.angle_beta_buttonm.clicked.connect(rot_beta_m)
	ui.angle_z_buttonp.clicked.connect(rot_z_p)
	ui.angle_z_buttonm.clicked.connect(rot_z_m)
	ui.rot_gm_button.clicked.connect(rotgm)
	ui.rot_gp_button.clicked.connect(rotgp)
	ui.lock_checkButton.stateChanged.connect(lock)
	ui.addpole_button.clicked.connect(addpole)
	ui.undo_addpole_button.clicked.connect(undo_addpole)
	ui.sym_button.clicked.connect(addpole_sym)
	ui.undo_sym_button.clicked.connect(undo_sym)
	ui.trace_plan_button.clicked.connect(trace_addplan)
	ui.undo_trace_plan_button.clicked.connect(undo_trace_addplan)
	ui.trace_cone_button.clicked.connect(trace_addcone)
	ui.undo_trace_cone_button.clicked.connect(undo_trace_addcone)
	ui.trace_plan_sym_button.clicked.connect(trace_plan_sym)
	ui.undo_trace_plan_sym_button.clicked.connect(undo_trace_plan_sym)
	ui.trace_schmid_button.clicked.connect(schmid_trace)
	ui.undo_trace_schmid.clicked.connect(undo_schmid_trace)
	ui.norm_button.clicked.connect(dhkl)
	ui.dm_button.clicked.connect(dm)
	ui.dp_button.clicked.connect(dp)
	ui.reset_view_button.clicked.connect(reset_view)
	figure.canvas.mpl_connect('motion_notify_event', coordinates)
	figure.canvas.mpl_connect('button_press_event', click_a_pole)

# Initialize variables
	
	dmip=0
	tr_schmid=np.zeros((1,3))
	var_lock=0
	ui.lock_checkButton.setChecked(False)
	ui.color_trace_bleu.setChecked(True)
	ui.wulff_button.setChecked(True)
	ui.wulff_button.setChecked(True)
	ui.d_label_var.setText('0')
	ui.alpha_entry.setText('90')
	ui.beta_entry.setText('90')
	ui.gamma_entry.setText('90')
	ui.a_entry.setText('1')
	ui.b_entry.setText('1')
	ui.c_entry.setText('1')
	ui.phi1_entry.setText('0')
	ui.phi_entry.setText('0')
	ui.phi2_entry.setText('0')
	ui.e_entry.setText('1')
	ui.rg_label.setText('0.0')
	ui.angle_euler_label.setText(' ')
	ui.size_var.setText('40')
	ui.e_entry.setText('1')
	ui.angle_alpha_entry.setText('5')
	ui.angle_beta_entry.setText('5')
	ui.angle_z_entry.setText('5')
	ui.angle_beta_entry.setText('5')
	ui.angle_z_entry.setText('5')	
	ui.d_entry.setText('1')
	ui.rot_g_entry.setText('5')
	ui.inclination_entry.setText('30')
	a = figure.add_subplot(111)
	wulff()	
	Index.show()
	sys.exit(app.exec_())




