#!/usr/bin/python

######################################################################
#
#
# Stereo-Proj is a python utility to plot stereographic projetion of a given crystal. It is designed
# to be used in electron microscopy experiments.
# Author: F. Mompiou, CEMES-CNRS
#
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
import hkl_uvwUI
import widthUI
import kikuchiUI
                 

################
#       Misc
################

def unique_rows(a):
    a = np.ascontiguousarray(a)
    unique_a = np.unique(a.view([('', a.dtype)]*a.shape[1]))
    return unique_a.view(a.dtype).reshape((unique_a.shape[0], a.shape[1]))

def GCD(a, b, rtol = 1e-05, atol = 1e-08):
    t = min(abs(a), abs(b))
    while abs(b) > rtol * t + atol:
        a, b = b, a % b
    return a
  

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

def proj_gnomonic(x,y,z): 
  
    if z==0: 
        X=x
        Y=y
    
    else: 
            
        X=x/z
        Y=y/z
    
    return np.array([X,Y],float) 

#def proj_ortho(x,y,z): 
#        
#    return np.array([x,y],float) 

         
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
   th=th*np.pi/180
   no=np.linalg.norm([a,b,c])
   aa=a/no
   bb=b/no
   cc=c/no
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
    global axes,axesh,D,Dstar,V,G
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])*1e-10
    b=np.float(abc[1])*1e-10
    c=np.float(abc[2])*1e-10
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alpha=np.float(alphabetagamma[0])
    beta=np.float(alphabetagamma[1])
    gamma=np.float(alphabetagamma[2])
    e=np.int(ui.e_entry.text())
    d2=np.float(ui.d_label_var.text())
    alpha=alpha*np.pi/180
    beta=beta*np.pi/180
    gamma=gamma*np.pi/180
    V=a*b*c*np.sqrt(1-(np.cos(alpha)**2)-(np.cos(beta))**2-(np.cos(gamma))**2+2*np.cos(alpha)*np.cos(beta)*np.cos(gamma))
    D=np.array([[a,b*np.cos(gamma),c*np.cos(beta)],[0,b*np.sin(gamma),  c*(np.cos(alpha)-np.cos(beta)*np.cos(gamma))/np.sin(gamma)],[0,0,V/(a*b*np.sin(gamma))]])
    Dstar=np.transpose(np.linalg.inv(D))
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])    
    axes=np.zeros(((2*e+1)**3-1,3))
    axesh=np.zeros(((2*e+1)**3-1,7))
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
				            axesh[id,3]=0
				else:
			 		    Ma=np.dot(D,np.array([i,j,k],float))
			 		    axesh[id,3]=1
			 	
				m=np.abs(reduce(lambda x,y:GCD(x,y),[i,j,k]))
				if (np.around(i/m)==i/m) & (np.around(j/m)==j/m) & (np.around(k/m)==k/m):
					axes[id,:]=np.array([i,j,k])/m
				else:
					axes[id,:]=np.array([i,j,k])
				axesh[id,0:3]=Ma/np.linalg.norm(Ma)
				axesh[id,5]=1
				axesh[id,6]=1
			       	id=id+1
    
    axesh=axesh[~np.all(axesh[:,0:3]==0, axis=1)]
    axes=axes[~np.all(axes==0, axis=1)]

    return axes,axesh,D,Dstar,V,G

###############################################
#
# Switch to reciprocal indices with size indicating the intensity
#  Need as input a file with the atoms in the cells to get the structure factor
#
###############################################
 
def lattice_reciprocal():
 	if ui.reciprocal_checkBox.isChecked():
 		crist_reciprocal()
 	else:
 		undo_crist_reciprocal()
 		
    
def crist_reciprocal():
	global axes,axesh, naxes
	
	for z in range(0, np.shape(axes)[0]):
		if z<(np.shape(axes)[0]-naxes):
			I,h,k,l=extinction(ui.space_group_Box.currentText(),axes[z,0],axes[z,1],axes[z,2],np.int(ui.e_entry.text()),0)
		else:
			I,h,k,l=extinction(ui.space_group_Box.currentText(),axes[z,0],axes[z,1],axes[z,2],10000,0)
		
		if I>0:
		 	if var_uvw()==0:      
		 		axesh[z,3]=0
		 	else:
		 		axesh[z,3]=1
        	        axesh[z,5]=I
        	        axesh[z,6]=1
        	        axes[z,:]=np.array([h,k,l])
		else:
			axesh[z,0:3]=np.array([0,0,0])
			if var_uvw()==0:      
		 		axesh[z,3]=0
		 	else:
		 		axesh[z,3]=1
        	        axesh[z,5]=1
        	        axesh[z,6]=1
        	        axes[z,:]=np.array([0,0,0])
        axesh=axesh[~np.all(axesh[:,0:3]==0, axis=1)]
    	axes=axes[~np.all(axes==0, axis=1)]
    	
    	return axes,axesh,naxes

def undo_crist_reciprocal():
	global axes,axesh,naxes,dmip
	if naxes!=0:
		extra_axes=axes[-naxes:,:]
		extra_axesh=axesh[-naxes:,:]
		for i in range(0,np.shape(extra_axes)[0]):
			m=reduce(lambda x,y:GCD(x,y),extra_axes[i,:])
			extra_axes[i,:]=extra_axes[i,:]/m
			if var_uvw()==0:      
		 		extra_axesh[i,3]=0
		 	else:
		 		extra_axesh[i,3]=1
		 	extra_axesh[i,5]=1
		 	extra_axesh[i,6]=1
			
		crist()
		axes=np.vstack((axes,extra_axes))
		axesh=np.vstack((axesh,extra_axesh))
	else:
		crist()
		
	return axes, axesh,naxes

def extinction(space_group,h,k,l,lim,diff):
    global x_space,G,x_scatt
    
    h0=h
    k0=k
    l0=l
   
    for i in range(0,len(x_space)):
        if space_group==x_space[i][0]:
            s0=i
   
    while np.amax([np.abs(h0),np.abs(k0),np.abs(l0)])<=lim:
    	    F=0
    	    s=s0
    	    
	    while (s<(len(x_space)-1) and (len(x_space[s+1])==4)):
	    		q=2*np.pi*np.sqrt(np.dot(np.array([h0,k0,l0]),np.dot(np.linalg.inv(G),np.array([h0,k0,l0]))))*1e-10
	    		f=str(x_space[s+1][0])
	    		for z in range(0,len(x_scatt)):
	    			
	    			if f==x_scatt[z][0]:
	    				f=eval(x_scatt[z][1])*np.exp(-eval(x_scatt[z][2])*(q/4/np.pi)**2)+eval(x_scatt[z][3])*np.exp(-eval(x_scatt[z][4])*(q/4/np.pi)**2)+eval(x_scatt[z][5])*np.exp(-eval(x_scatt[z][6])*(q/4/np.pi)**2)+eval(x_scatt[z][7])*np.exp(-eval(x_scatt[z][8])*(q/4/np.pi)**2)+eval(x_scatt[z][9])
	    			
			
			F=F+f*np.exp(2j*np.pi*(eval(x_space[s+1][1])*h0+eval(x_space[s+1][2])*k0+eval(x_space[s+1][3])*l0))        
			s=s+1
			
	    
	    I=np.around(float(np.real(F*np.conj(F))),decimals=2)
	    if diff==0:
		    if I>0:
		    	break
		    else:
		    	h0=2*h0
		    	k0=2*k0
		    	l0=2*l0
	    else: 
	    		break
    
    return I,h0,k0,l0



######################################################
#
# Reduce number of poles/directions as a function of d-spacing (plus or minus)
#
#######################################################
def dist_restrict():
	global G,axes,axesh
	abc=ui.abc_entry.text().split(",")
    	a=np.float(abc[0])*1e-10
    	b=np.float(abc[1])*1e-10
    	c=np.float(abc[2])*1e-10
	d2=np.float(ui.d_label_var.text())
	for i in range(0,np.shape(axes)[0]):
    		d=1/(np.sqrt(np.dot(axes[i,:],np.dot(np.linalg.inv(G),axes[i,:]))))
    		if d<d2*0.1*np.amax([a,b,c]):
    			axesh[i,6]=0
    		else:
    			axesh[i,6]=1
    	
    	trace()

def dm():
    global dmip
    
    dmip=dmip-np.float(ui.d_entry.text())
    ui.d_label_var.setText(str(dmip))
    dist_restrict()   
    
    return dmip
    
def dp():
    global dmip, a,axes,axesh
    
    dmip=dmip+np.float(ui.d_entry.text())
    ui.d_label_var.setText(str(dmip))
    dist_restrict()
    
    return dmip 
    

    
####################################################################
#
#  Plot iso-schmid factor, ie for a given plan the locus of b with a given schmid factor (Oy direction
# assumed to be the straining axis
#
####################################################################

def schmid_trace():
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid,a,minx,maxx,miny,maxy,trC
    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
            
    tr_schmid=np.vstack((tr_schmid,np.array([pole1,pole2,pole3])))
    trace()
    
def undo_schmid_trace():
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid,a,minx,maxx,miny,maxy,trC
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    
    tr_s=tr_schmid
    for i in range(1,tr_schmid.shape[0]):
		if tr_schmid[i,0]==pole1 and tr_schmid[i,1]==pole2 and tr_schmid[i,2]==pole3:
			tr_s=np.delete(tr_schmid,i,0)
    tr_schmid=tr_s
    trace()

def fact(angle,r,t,n):
	t_ang=ang_work_space()
	x=r*np.cos(t)/n
	y=r*np.sin(t)/n
	C=np.dot(Rot(t_ang,0,0,1),np.array([x,y,0]))
	x=C[0]
	y=C[1]
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
        t_ang=-ang_work_space()
        T=np.dot(Rot(t_ang,0,0,1),np.array([0,1,0]))
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
# of the sample are locked to the crystal axes when the check box is ticked.
# It mimics double-tilt holder (rotation of alpha along fixed x and rotation of beta along the beta tilt moving axis)
# or  tilt-rotation holder  (rotation of alpha along fixed # x and rotation of z along the z-rotation moving axis).
#
##########################################################################
def euler_label():
	global M
	if np.abs(M[2,2]-1)<0.0001:
		phir=0
		phi1r=0
		phi2r=np.arctan2(M[1,0],M[0,0])*180/np.pi
	else:
		phir=np.arccos(M[2,2])*180/np.pi
		phi2r=np.arctan2(M[2,0],M[2,1])*180/np.pi
		phi1r=np.arctan2(M[0,2],-M[1,2])*180/np.pi
	    
        t=str(np.around(phi1r,decimals=1))+str(',')+str(np.around(phir,decimals=1))+str(',')+str(np.around(phi2r,decimals=1))
        ui.angle_euler_label.setText(t)
        
def lock():
	global M, var_lock,M_lock
        
        if ui.lock_checkButton.isChecked():
                var_lock=1
                M_lock=M
        else:
        	var_lock,M_lock=0,0

        return var_lock,M_lock


def rot_alpha_p():
    global angle_alpha,M,a,trP,trC,s_a

    tha=s_a*np.float(ui.angle_alpha_entry.text())
    t_ang=-ang_work_space()
    t_a_y=np.dot(Rot(t_ang,0,0,1),np.array([0,1,0]))
    M=np.dot(Rot(tha,t_a_y[0],t_a_y[1],t_a_y[2]),M)
    trace()
    euler_label()
    angle_alpha=angle_alpha+np.float(ui.angle_alpha_entry.text())
    ui.angle_alpha_label_2.setText(str(angle_alpha))
    return angle_alpha,M
    
    
def rot_alpha_m():
    global angle_alpha,M,a,trP,trC,s_a

    tha=-s_a*np.float(ui.angle_alpha_entry.text())
    t_ang=-ang_work_space()
    t_a_y=np.dot(Rot(t_ang,0,0,1),np.array([0,1,0]))
    M=np.dot(Rot(tha,t_a_y[0],t_a_y[1],t_a_y[2]),M)
    trace()
    euler_label()
    angle_alpha=angle_alpha-np.float(ui.angle_alpha_entry.text())
    ui.angle_alpha_label_2.setText(str(angle_alpha))
    return angle_alpha,M

    
def rot_beta_m():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock,s_b
    t_ang=-ang_work_space()
    t_a_x=np.dot(Rot(t_ang,0,0,1),np.array([1,0,0]))
    
    if var_lock==0:
    	AxeY=t_a_x
    else:
   	A=np.dot(np.linalg.inv(M_lock),t_a_x)
	AxeY=np.dot(M,A)
    
    thb=-s_b*np.float(ui.angle_beta_entry.text())
    M=np.dot(Rot(thb,AxeY[0],AxeY[1],AxeY[2]),M)
    trace()
    euler_label()
    angle_beta=angle_beta-np.float(ui.angle_beta_entry.text())
    ui.angle_beta_label_2.setText(str(angle_beta))
    return angle_beta,M   
   
def rot_beta_p():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock,s_b
    t_ang=-ang_work_space()
    t_a_x=np.dot(Rot(t_ang,0,0,1),np.array([1,0,0]))
    if var_lock==0:
    	AxeY=t_a_x
    else:
   	A=np.dot(np.linalg.inv(M_lock),t_a_x)
	AxeY=np.dot(M,A)
    
    thb=s_b*np.float(ui.angle_beta_entry.text())
    M=np.dot(Rot(thb,AxeY[0],AxeY[1],AxeY[2]),M)
    trace()
    euler_label()
    angle_beta=angle_beta+np.float(ui.angle_beta_entry.text())
    ui.angle_beta_label_2.setText(str(angle_beta))
    return angle_beta,M   

def rot_z_m():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock,s_z
   
    if var_lock==0:
    	AxeZ=np.array([0,0,1])
    else:
   	A=np.dot(np.linalg.inv(M_lock),np.array([0,0,1]))
	AxeZ=np.dot(M,A)
    
    thz=-s_z*np.float(ui.angle_z_entry.text())
    M=np.dot(Rot(thz,AxeZ[0],AxeZ[1],AxeZ[2]),M)
    trace()
    euler_label()
    angle_z=angle_z-np.float(ui.angle_z_entry.text())
    ui.angle_z_label_2.setText(str(angle_z))
    return angle_z,M      
   
def rot_z_p():
    global angle_beta,M,angle_alpha, angle_z, var_lock, M_lock,s_z
   
    if var_lock==0:
    	AxeZ=np.array([0,0,1])
    else:
   	A=np.dot(np.linalg.inv(M_lock),np.array([0,0,1]))
	AxeZ=np.dot(M,A)
	
    thz=s_z*np.float(ui.angle_z_entry.text())
    M=np.dot(Rot(thz,AxeZ[0],AxeZ[1],AxeZ[2]),M)
    trace()
    euler_label()
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
    diff=ui.diff_entry.text().split(",")
    diff1=np.float(diff[0])
    diff2=np.float(diff[1])
    diff3=np.float(diff[2])
    A=np.array([diff1,diff2,diff3])
    Ad=np.dot(Dstar,A)    
    Ap=np.dot(M,Ad)/np.linalg.norm(np.dot(M,Ad))
    M=np.dot(Rot(thg,Ap[0],Ap[1],Ap[2]),M)
    trace()    
    euler_label()
    g=g-np.float(ui.rot_g_entry.text())
    ui.rg_label.setText(str(g))
    return g,M
    
def rotgp():
    global g,M,D

    thg=np.float(ui.rot_g_entry.text())
    diff=ui.diff_entry.text().split(",")
    diff1=np.float(diff[0])
    diff2=np.float(diff[1])
    diff3=np.float(diff[2])
    A=np.array([diff1,diff2,diff3])
    Ad=np.dot(Dstar,A)    
    Ap=np.dot(M,Ad)/np.linalg.norm(np.dot(M,Ad))
    M=np.dot(Rot(thg,Ap[0],Ap[1],Ap[2]),M)
    trace()    
    euler_label()
    g=g+np.float(ui.rot_g_entry.text())
    ui.rg_label.setText(str(g))
    return g,M



####################################################################
#
# Add a given pole and equivalent ones
#
####################################################################

def pole(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,naxes
    
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
     
    T=np.vstack((T,np.array([S[0],S[1],S[2]])))

    if ui.reciprocal_checkBox.isChecked():
	I,h,k,l=extinction(ui.space_group_Box.currentText(),pole1,pole2,pole3,100000,0)

	if I>0:
		axes=np.vstack((axes,np.array([h,k,l])))
		axes=np.vstack((axes,np.array([-h,-k,-l])))
		if var_uvw()==0 :
			axesh=np.vstack((axesh,np.array([Gsh[0],Gsh[1],Gsh[2],0,color_trace(),I,1])))
			axesh=np.vstack((axesh,np.array([-Gsh[0],-Gsh[1],-Gsh[2],0,color_trace(),I,1])))
		else:
			axesh=np.vstack((axesh,np.array([Gsh[0],Gsh[1],Gsh[2],1,color_trace(),I,1])))
			axesh=np.vstack((axesh,np.array([-Gsh[0],-Gsh[1],-Gsh[2],1,color_trace(),I,1])))
		
    else:
	axes=np.vstack((axes,np.array([pole1,pole2,pole3])))
	axes=np.vstack((axes,np.array([-pole1,-pole2,-pole3])))
	if var_uvw()==0 :
		axesh=np.vstack((axesh,np.array([Gsh[0],Gsh[1],Gsh[2],0,color_trace(),0,1])))
		axesh=np.vstack((axesh,np.array([-Gsh[0],-Gsh[1],-Gsh[2],0,color_trace(),0,1])))
	else:
		axesh=np.vstack((axesh,np.array([Gsh[0],Gsh[1],Gsh[2],1,color_trace(),0,1])))
		axesh=np.vstack((axesh,np.array([-Gsh[0],-Gsh[1],-Gsh[2],1,color_trace(),0,1])))
	
    naxes=naxes+2
   
    return axes,axesh,T,naxes

def undo_pole(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,naxes
    
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
    
    if ui.reciprocal_checkBox.isChecked():
	I,h,k,l=extinction(ui.space_group_Box.currentText(),pole1,pole2,pole3,100000,0)
	if I>0:
		pole1=h
		pole2=k
		pole3=l
		ind=np.where((axes[:,0]==pole1) & (axes[:,1]==pole2)& (axes[:,2]==pole3)|(axes[:,0]==-pole1) & (axes[:,1]==-pole2)& (axes[:,2]==-pole3))
    	
    else:
    	m=reduce(lambda x,y:GCD(x,y),[pole1,pole2,pole3])
    	ind=np.where((axes[:,0]==pole1) & (axes[:,1]==pole2)& (axes[:,2]==pole3)|(axes[:,0]==-pole1) & (axes[:,1]==-pole2)& (axes[:,2]==-pole3))
    axes=np.delete(axes,ind,0)
    T=np.delete(T,ind,0)
    axesh=np.delete(axesh,ind,0)
    naxes=naxes-2
    return axes,axesh,T,naxes

    
def d(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])
    b=np.float(abc[1])
    c=np.float(abc[2])
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alpha=np.float(alphabetagamma[0])*np.pi/180
    beta=np.float(alphabetagamma[1])*np.pi/180
    gamma=np.float(alphabetagamma[2])*np.pi/180
    G=np.array([[a**2,a*b*np.cos(gamma),a*c*np.cos(beta)],[a*b*np.cos(gamma),b**2,b*c*np.cos(alpha)],[a*c*np.cos(beta),b*c*np.cos(alpha),c**2]])    
    ds=(np.sqrt(np.dot(np.array([pole1,pole2,pole3]),np.dot(np.linalg.inv(G),np.array([pole1,pole2,pole3])))))
    return ds
    
def addpole_sym():
    global M,axes,axesh,T,V,D,Dstar,G
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])
    b=np.float(abc[1])
    c=np.float(abc[2])
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alpha=np.float(alphabetagamma[0])*np.pi/180
    beta=np.float(alphabetagamma[1])*np.pi/180
    gamma=np.float(alphabetagamma[2])*np.pi/180
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
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])
    b=np.float(abc[1])
    c=np.float(abc[2])
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alpha=np.float(alphabetagamma[0])*np.pi/180
    beta=np.float(alphabetagamma[1])*np.pi/180
    gamma=np.float(alphabetagamma[2])*np.pi/180
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
    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    pole(pole1,pole2,pole3)
    trace()
    
def undo_addpole():
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid,nn,trC
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
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
            pole1=2*pole1+pole2
            pole2=2*pole2+pole1
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
            pole1=2*pole1+pole2
            pole2=2*pole2+pole1
            pole_i=1
    trC=np.vstack((trC,np.array([pole1,pole2,pole3,pole_i,pole_c,inc])))
    b=np.ascontiguousarray(trC).view(np.dtype((np.void, trC.dtype.itemsize * trC.shape[1])))
    trC=np.unique(b).view(trC.dtype).reshape(-1, trC.shape[1])

    
def trace_addplan():
    global M,axes,axesh,T,V,D,Dstar,trP
    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
        
    trace_plan(pole1,pole2,pole3)
    trace_plan2
    trace()

def trace_addcone():
    global M,axes,axesh,T,V,D,Dstar,trC
    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
        
    trace_cone(pole1,pole2,pole3)
    trace()
    
def undo_trace_addplan():
    global M,axes,axesh,T,V,D,Dstar,trP
    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    
    undo_trace_plan(pole1,pole2,pole3)
    trace()

def undo_trace_addcone():
    global M,axes,axesh,T,V,D,Dstar,trC
    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
        
    undo_trace_cone(pole1,pole2,pole3)
    trace()
    
def undo_trace_plan(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,trP,tr_schmid
    
    ind=np.where((trP[:,0]==pole1) & (trP[:,1]==pole2)& (trP[:,2]==pole3)|(trP[:,0]==-pole1) & (trP[:,1]==-pole2)& (trP[:,2]==-pole3))
    
    trP=np.delete(trP,ind,0)
    b=np.ascontiguousarray(trP).view(np.dtype((np.void, trP.dtype.itemsize * trP.shape[1])))
    trP=np.unique(b).view(trP.dtype).reshape(-1, trP.shape[1])
    
def undo_trace_cone(pole1,pole2,pole3):
    global M,axes,axesh,T,V,D,Dstar,trC,tr_schmid
    
    ind=np.where((trC[:,0]==pole1) & (trC[:,1]==pole2)& (trC[:,2]==pole3)|(trC[:,0]==-pole1) & (trC[:,1]==-pole2)& (trC[:,2]==-pole3))
    trC=np.delete(trC,ind,0)
    b=np.ascontiguousarray(trC).view(np.dtype((np.void, trC.dtype.itemsize * trC.shape[1])))
    
    trC=np.unique(b).view(trC.dtype).reshape(-1, trC.shape[1])



def trace_plan_sym():
    global M,axes,axesh,T,V,D,Dstar,G    
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])*1e-10
    b=np.float(abc[1])*1e-10
    c=np.float(abc[2])*1e-10
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alpha=np.float(alphabetagamma[0])*np.pi/180
    beta=np.float(alphabetagamma[1])*np.pi/180
    gamma=np.float(alphabetagamma[2])*np.pi/180
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
    pole_entry=ui.pole_entry.text().split(",")
    pole1=np.float(pole_entry[0])
    pole2=np.float(pole_entry[1])
    pole3=np.float(pole_entry[2])
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])*1e-10
    b=np.float(abc[1])*1e-10
    c=np.float(abc[2])*1e-10
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alpha=np.float(alphabetagamma[0])*np.pi/180;
    beta=np.float(alphabetagamma[1])*np.pi/180;
    gamma=np.float(alphabetagamma[2])*np.pi/180;
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
        t=np.arctan2(S[1],S[0])*180/np.pi
        w=0
        ph=np.arccos(S[2]/r)*180/np.pi
	
        for g in np.linspace(-np.pi,np.pi,100):
    		Aa=np.dot(Rot(t,0,0,1),np.dot(Rot(ph,0,1,0),np.array([np.sin(g),np.cos(g),0])))
    		A[:,w]=proj(Aa[0],Aa[1],Aa[2])*300
    		Q=np.vstack((Q,A[:,w]))
    		w=w+1
        
        Q=np.delete(Q,0,0)   
	if B[h,4]==1:
		a.plot(Q[:,0]+300,Q[:,1]+300,'g')
	if B[h,4]==2:
		a.plot(Q[:,0]+300,Q[:,1]+300,'b')
	if B[h,4]==3:
		a.plot(Q[:,0]+300,Q[:,1]+300,'r')
       
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
        t=np.arctan2(S[1],S[0])*180/np.pi
        w=0
        ph=np.arccos(S[2]/r)*180/np.pi
	

        for g in np.linspace(-np.pi,np.pi,100):
    		Aa=np.dot(Rot(t,0,0,1),np.dot(Rot(ph,0,1,0),np.array([np.sin(g)*np.sin(i*np.pi/180),np.cos(g)*np.sin(i*np.pi/180),np.cos(i*np.pi/180)])))
    		A[:,w]=proj2(Aa[0],Aa[1],Aa[2])*300
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
			a.plot(Q[int(wp[tt]):int(wp[tt+1]),0]+300,Q[int(wp[tt]):int(wp[tt+1]),1]+300,'g')
		if B[h,4]==2:
			a.plot(Q[int(wp[tt]):int(wp[tt+1]),0]+300,Q[int(wp[tt]):int(wp[tt+1]),1]+300,'b')
		if B[h,4]==3:
			a.plot(Q[int(wp[tt]):int(wp[tt+1]),0]+300,Q[int(wp[tt]):int(wp[tt+1]),1]+300,'r')
            
            
        
####################################################################
#
# Click a pole 
#
####################################################################    

def click_a_pole(event):
        
    global M,Dstar,D,minx,maxx,miny,maxy,a,Stc
      
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
            if var_uvw()==0:
                        A=np.dot(np.linalg.inv(Dstar),A)*1e10*100
            else:
            		A=np.dot(np.linalg.inv(D),A)*1e-10*100
		    	if var_hexa()==1:
       				Aa=(2*A[0]-A[1])/3
        			Ab=(2*A[1]-A[0])/3
            			A[0]=Aa
            			A[1]=Ab
						
            		
            pole(A[0],A[1],A[2])
            Stc=np.vstack((Stc, np.array([A[0],A[1],A[2]])))
            trace()                
                
def undo_click_a_pole():
	global Stc
	undo_pole(Stc[-1,0],Stc[-1,1],Stc[-1,2])
	Stc=Stc[:-1,:]
	trace()

####################################################################
#
# Inclinaison-beta indicator when the mouse is on the stereo
#
#################################################################### 
  
def coordinates(event):
    t_ang=ang_work_space()*np.pi/180
    if event.xdata and event.ydata:
	    x=event.xdata
	    y=event.ydata    
	    x=(x-300)/300
	    y=(y-300)/300
	    X0=2*x/(1+x**2+y**2)
            Y0=2*y/(1+x**2+y**2)
            Z0=(-1+x**2+y**2)/(1+x**2+y**2)
            Rxyz=np.dot(Rot(t_ang*180/np.pi,0,0,1),[X0,Y0,Z0])
            X=Rxyz[0]
            Y=Rxyz[1]
            Z=Rxyz[2]
            lat=np.arctan2(np.sqrt(X**2+Z**2),Y)*180/np.pi
            if X<0:
            	lat=-lat
            longi=-np.arctan2(Z,X)*180/np.pi
            if ui.alpha_signBox.isChecked():
            	longi=-longi
	    if np.abs(longi)>90:
	     	if longi>0:
	     		longi=longi-180
	     	else:
	     		longi=longi+180
	
	    c=str(np.around(longi,decimals=1))+str(',')+str(np.around(lat,decimals=1))
	    ui.coord_label.setText(str(c))

########################################################
#
# Calculate interplanar distance 
#
#######################################################

def dhkl():
    pole_entry=ui.pole_entry.text().split(",")
    i=np.float(pole_entry[0])
    j=np.float(pole_entry[1])
    k=np.float(pole_entry[2])
    abc=ui.abc_entry.text().split(",")
    a=np.float(abc[0])
    b=np.float(abc[1])
    c=np.float(abc[2])
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alp=np.float(alphabetagamma[0])*np.pi/180
    bet=np.float(alphabetagamma[1])*np.pi/180
    gam=np.float(alphabetagamma[2])*np.pi/180
    G=np.array([[a**2,a*b*np.cos(gam),a*c*np.cos(bet)],[a*b*np.cos(gam),b**2,b*c*np.cos(alp)],[a*c*np.cos(bet),b*c*np.cos(alp),c**2]])    
    d=np.around(1/(np.sqrt(np.dot(np.array([i,j,k]),np.dot(np.linalg.inv(G),np.array([i,j,k]))))), decimals=3)
    ui.dhkl_label.setText(str(d))
    return        

####################################################################
#
# Reset view after zoom/update axes/angles
#
#################################################################### 

def reset_view():
	global a
	
	a.axis([minx,maxx,miny,maxy])
	mpl.rcParams['font.size'] = ui.text_size_entry.text()
	trace()

def tilt_axes():
	global s_a,s_b,s_z
	s_a,s_b,s_z=1,1,1
	if ui.alpha_signBox.isChecked():
		s_a=-1
	if ui.beta_signBox.isChecked():
		s_b=-1
	if ui.theta_signBox.isChecked():
    		s_b=-1
        return s_a,s_b,s_z

####################
#
# define work space (real or reciprocal) to take tilt/y axis angles into account
#
######################
	
def ang_work_space():
	if ui.real_space_checkBox.isChecked():
		t_ang=np.float(ui.image_angle_entry.text())
	else:
		t_ang=np.float(ui.tilt_angle_entry.text())
	return t_ang
	
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
		img=img.rotate(float(ang_work_space()), fillcolor='white')
		img= np.array(img)
	else:
		img = 255*np.ones([600,600,3],dtype=np.uint8)
		circle = plt.Circle((300, 300), 300, color='black',fill=False)
		a.add_artist(circle)
		a.plot(300,300,'+',markersize=10,mew=3,color='black')
	
	a.imshow(img,interpolation="bicubic")
	#a.axis('off')
	plt.tight_layout()	
	figure.subplots_adjust(left=0.1,right=0.9, bottom=0.05,top=0.95, hspace=0.2,wspace=0.2)
    	a.figure.canvas.draw()  
	
def text_label(A,B):
	Aa=A[0]
	Ab=A[1]
	Ac=A[2]
	if B[3]==1 & var_hexa()==1:
		Aa=(2*A[0]-A[1])/3
		Ab=(2*A[1]-A[0])/3
		
	
	if np.sign(Aa)<0:
		s0=r'$\overline{'+str(np.abs(int(Aa)))+'}$'
	else:
		s0=str(np.abs(int(Aa)))
	if np.sign(Ab)<0:
		s1=r'$\overline{'+str(np.abs(int(Ab)))+'}$'
	else:
		s1=str(np.abs(int(Ab)))
	if np.sign(Ac)<0:
		s2=r'$\overline{'+str(np.abs(int(Ac)))+'}$'
	else:
		s2=str(np.abs(int(Ac)))
	s=s0+','+s1+','+s2
	if var_hexa()==1:
		if np.sign(-Aa-Ab)<0:
			s3=r'$\overline{'+str(int(np.abs(-Aa-Ab)))+'}$'
		else:
			s3=str(int(np.abs(-Aa-Ab)))
		s=s0+','+s1+','+s3+','+s2
	if B[3]==1:
		s='['+s+']'
	return s
		
		

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
    global T,x,y,z,axes,axesh,M,trP,a,trC,s_a,s_b,s_z
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
    tilt_axes()
    for i in range(0,axes.shape[0]):
    	if axesh[i,6]==1:
		axeshr=np.array([axesh[i,0],axesh[i,1],axesh[i,2]])
		T[i,:]=np.dot(M,axeshr)
		P[i,:]=proj(T[i,0],T[i,1],T[i,2])*300
		
		if axesh[i,4]==1:
		    C.append('g')
		if axesh[i,4]==2:
		    C.append('b')
		if axesh[i,4]==3:
		    C.append('r')

		s=text_label(axes[i,:],axesh[i,:])
		a.annotate(s,(P[i,0]+300,P[i,1]+300))
    if ui.reciprocal_checkBox.isChecked():
    	if np.shape(axes)[0]>0:
    		s0=axesh[:,6]*axesh[:,5]/np.amax(axesh[:,5])
    	else:
    		s0=axesh[:,6]
    else:
    	s0=axesh[:,6]

    if var_carre()==0:           
        a.scatter(P[:,0]+300,P[:,1]+300,c=C,s=s0*np.float(ui.size_var.text()))
    else:
        a.scatter(P[:,0]+300,P[:,1]+300,edgecolor=C, s=s0*np.float(ui.size_var.text()), facecolors='none', linewidths=1.5)               

    
    a.axis([minx,maxx,miny,maxy])
    wulff()
    
 ####################################
 #
 # Initial plot from a given diffraction
 #
 ####################################
 
def princ():
    global T,angle_alpha, angle_beta, angle_z,M,Dstar,D,g,M0,trP,axeshr,nn,a,minx,maxx,miny,maxy,trC,Stc, naxes,dmip,tr_schmid,s_a,s_b,s_z
    trP=np.zeros((1,5))
    trC=np.zeros((1,6))
    Stc=np.zeros((1,3))
    tr_schmid=np.zeros((1,3))
    dmip=0
    naxes=0
    crist() 
    tilt_axes()
    if ui.reciprocal_checkBox.isChecked():
    	crist_reciprocal()
    a = figure.add_subplot(111)
    a.figure.clear()
    a = figure.add_subplot(111)
     
    diff=ui.diff_entry.text().split(",")
    diff1=np.float(diff[0])
    diff2=np.float(diff[1])
    diff3=np.float(diff[2])
    tilt=ui.tilt_entry.text().split(",")
    tilt_a=np.float(tilt[0])
    tilt_b=np.float(tilt[1])
    tilt_z=np.float(tilt[2])
    inclinaison=np.float(ui.inclinaison_entry.text())    
    diff_ang=-ang_work_space()
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
    
    R=np.dot(Rot(diff_ang,0,0,1),np.dot(Rot(-s_z*tilt_z,0,0,1),np.dot(Rot(-s_b*tilt_b,1,0,0),np.dot(Rot(-s_a*tilt_a,0,1,0),np.dot(Rot(-inclinaison,0,0,1),Rot(ang*180/np.pi, normal[0],normal[1],normal[2]))))))    
       
    P=np.zeros((axes.shape[0],2))
    T=np.zeros((axes.shape))
    nn=axes.shape[0]
    C=[]
    for i in range(0,axes.shape[0]):
    	if axesh[i,5]!=-1:
		axeshr=np.array([axesh[i,0],axesh[i,1],axesh[i,2]])
		T[i,:]=np.dot(R,axeshr)
		P[i,:]=proj(T[i,0],T[i,1],T[i,2])*300
		axeshr=axeshr/np.linalg.norm(axeshr)
		
		if axesh[i,4]==1:
		    C.append('g')
		if axesh[i,4]==2:
		    C.append('b')
		if axesh[i,4]==3:
		    C.append('r')

		s=text_label(axes[i,:],axesh[i,:])
		a.annotate(s,(P[i,0]+300,P[i,1]+300))
    if ui.reciprocal_checkBox.isChecked():
    	if np.shape(axes)[0]>0:
    		s0=axesh[:,6]*axesh[:,5]/np.amax(axesh[:,5])
    	else:
    		s0=axesh[:,6]
    else:
    	s0=axesh[:,6]

    if var_carre()==0:           
        a.scatter(P[:,0]+300,P[:,1]+300,c=C,s=s0*np.float(ui.size_var.text()))
    else:
        a.scatter(P[:,0]+300,P[:,1]+300,edgecolor=C, s=s0*np.float(ui.size_var.text()), facecolors='none', linewidths=1.5)               
    
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
    euler_label()
    return T,angle_alpha,angle_beta,angle_z,g,M,M0
    
##############################################"
#
# Plot from Euler angle
#
##################################################"

def princ2():
    global T,angle_alpha,angle_beta,angle_z,M,Dstar,D,g,M0,trP,a,axeshr,nn,minx,maxx,miny,maxy,trC,Stc,naxes,dmip,tr_schmid,s_a,s_b,s_c
    
    trP=np.zeros((1,5))
    trC=np.zeros((1,6))
    Stc=np.zeros((1,3))
    tr_schmid=np.zeros((1,3))
    a = figure.add_subplot(111)
    a.figure.clear()
    a = figure.add_subplot(111)
    phi1phiphi2=ui.phi1phiphi2_entry.text().split(",")
    phi1=np.float(phi1phiphi2[0])
    phi=np.float(phi1phiphi2[1])
    phi2=np.float(phi1phiphi2[2])
    dmip=0
    naxes=0 
    crist()   
    tilt_axes()
    if ui.reciprocal_checkBox.isChecked():
    	crist_reciprocal()
        
    P=np.zeros((axes.shape[0],2))
    T=np.zeros((axes.shape))
    nn=axes.shape[0]
    C=[]    

    for i in range(0,axes.shape[0]):
        axeshr=np.array([axesh[i,0],axesh[i,1],axesh[i,2]])
        T[i,:]=np.dot(rotation(phi1,phi,phi2),axeshr)
        P[i,:]=proj(T[i,0],T[i,1],T[i,2])*300
        if color_trace()==1:
            C.append('g')
            axesh[i,4]=1
        if color_trace()==2:
            C.append('b')
            axesh[i,4]=2
        if color_trace()==3:
            C.append('r')
            axesh[i,4]=3

        s=text_label(axes[i,:],axesh[i,:])    
              
        a.annotate(s,(P[i,0]+300,P[i,1]+300))
    if ui.reciprocal_checkBox.isChecked():
    	s0=axesh[:,5]/np.amax(axesh[:,5])
    else:
    	s0=1
    if var_carre()==0:           
        a.scatter(P[:,0]+300,P[:,1]+300,c=C,s=s0*np.float(ui.size_var.text()))
    else:
        a.scatter(P[:,0]+300,P[:,1]+300,edgecolor=C, s=s0*np.float(ui.size_var.text()), facecolors='none', linewidths=1.5)       
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
    
    return T,angle_alpha,angle_beta,angle_z,g,M,naxes

  
  
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
    
    ui.abc_entry.setText(str(item[1])+','+str(item[2])+','+str(item[3]))
    ui.alphabetagamma_entry.setText(str(item[4])+','+str(item[5])+','+str(item[6]))
    
    ii=ui.space_group_Box.findText(str(item[7]))
    ui.space_group_Box.setCurrentIndex(ii)
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
	n1=ui_angle.n1_entry.text().split(",")
	c100=np.float(n1[0])
	c110=np.float(n1[1])
	c120=np.float(n1[2])
	n2=ui_angle.n2_entry.text().split(",")
	c200=np.float(n2[0])
	c210=np.float(n2[1])
	c220=np.float(n2[2])
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
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alp=np.float(alphabetagamma[0])*np.pi/180
    bet=np.float(alphabetagamma[1])*np.pi/180
    gam=np.float(alphabetagamma[2])*np.pi/180

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
    alphabetagamma=ui.alphabetagamma_entry.text().split(",")
    alp=np.float(alphabetagamma[0])*np.pi/180
    bet=np.float(alphabetagamma[1])*np.pi/180
    gam=np.float(alphabetagamma[2])*np.pi/180

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
    t_ang=-ang_work_space()
    T=np.dot(Rot(t_ang,0,0,1),T)
    anglen=np.arccos(np.dot(npr2,T)/np.linalg.norm(npr2))
    angleb=np.arccos(np.dot(bpr2,T)/np.linalg.norm(bpr2))
    s=np.cos(anglen)*np.cos(angleb)

    return s

def schmid_pole(pole1,pole2,pole3):
	global M,V,D,Dstar,G
	alphabetagamma=ui.alphabetagamma_entry.text().split(",")
        alp=np.float(alphabetagamma[0])*np.pi/180;
        bet=np.float(alphabetagamma[1])*np.pi/180;
        gam=np.float(alphabetagamma[2])*np.pi/180;
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
	n=ui_schmid.n_entry.text().split(",")
	h=np.float(n[0])
	k=np.float(n[1])
	l=np.float(n[2])
	b=ui_schmid.b_entry.text().split(",")
	u=np.float(b[0])
	v=np.float(b[1])
	w=np.float(b[2])
	n=np.array([h,k,l])
	b=np.array([u,v,w])
	T0=ui_schmid.T_entry.text().split(",")
	T=np.array([np.float(T0[0]),np.float(T0[1]),np.float(T0[2])])
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
# Calculating x,y,z direction and hkl<>uvw  (for xyz dialog box)
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
	return Xp,Yp,Zp
 
def to_uvw():
	global Dstar, D, M
	hkl=ui_hkl_uvw.hkl_entry.text().split(",")
	plane=np.array([np.float( hkl[0]),np.float(hkl[1]),np.float(hkl[2])])
	plane=plane/np.linalg.norm(plane)
	direction=np.dot(np.linalg.inv(D),np.dot(Dstar,plane))*1e-20
	if var_hexa()==1:
	            na=(2*direction[0]-direction[1])/3
		    n2a=(2*direction[1]-direction[0])/3
		    direction[0]=na
		    direction[1]=n2a
	ui_hkl_uvw.uvw_label.setText(str(np.round(100*direction[0],decimals=3))+', '+str(np.round(100*direction[1],decimals=3))+', '+str(np.round(100*direction[2],decimals=3)))
	
def to_hkl():
	global Dstar, D, M
	uvw=ui_hkl_uvw.uvw_entry.text().split(",")
	direction=np.array([np.float( uvw[0]),np.float(uvw[1]),np.float(uvw[2])])
	if var_hexa()==1:
	            na=2*direction[0]+direction[1]
		    n2a=2*direction[1]+direction[0]
		    direction[0]=na
		    direction[1]=n2a
	direction=direction/np.linalg.norm(direction)
	plane=np.dot(np.linalg.inv(Dstar),np.dot(D,direction))*1e20
	ui_hkl_uvw.hkl_label.setText(str(np.round(100*plane[0],decimals=3))+', '+str(np.round(100*plane[1],decimals=3))+', '+str(np.round(100*plane[2],decimals=3)))
	
	
##########################################################################
#
#  Apparent width class for dialog box: plot the width of a plane of given normal hkl with the tilt alpha angle. Plot trace direction with respect to the tilt axis
#
##########################################################################

 
def plot_width():
	global D, Dstar, M
#	ui_width.figure.clf()
	B=np.dot(np.linalg.inv(M),np.array([0,0,1]))
	plan=ui_width.plane_entry.text().split(",")
	n=np.array([np.float(plan[0]),np.float(plan[1]),np.float(plan[2])])
	nr=np.dot(Dstar,n)
	nr=nr/np.linalg.norm(nr)
	B=np.dot(Dstar,B)
	B=B/np.linalg.norm(B)
	la=np.zeros((1,41))
	la2=np.zeros((2,41))
	k=0
	t_ang=ang_work_space()
	if ui_width.surface_box.isChecked():
		s0=ui_width.foil_surface.text().split(",")
		s=np.array([np.float(s0[0]),np.float(s0[1]),np.float(s0[2])])
		T=np.cross(nr,s)
	else:	
		T=np.cross(nr,B)
	T=T/np.linalg.norm(T)

		
	for t in range(-40,41,2):
	    Mi=np.dot(Rot(t,0,1,0), np.dot(Rot(t_ang,0,0,1),M)) 
	    Bi=np.dot(np.linalg.inv(Mi),np.array([0,0,1]))
	    Bi=np.dot(Dstar,Bi)
	    Bi=Bi/np.linalg.norm(Bi)
	    Ti=np.dot(Mi,T)
	    la[0,k]=np.dot(nr,Bi)
	    la2[1,k]=np.arctan(Ti[0]/Ti[1])*180/np.pi
	    la2[0,k]=np.dot(nr,Bi)/np.sqrt(1-np.dot(T,Bi)**2)

	    k=k+1
	ax1 = figure_width.add_subplot(111)
	ax1.set_xlabel('alpha tilt angle')

	
	ax1.tick_params('y', colors='black')
	if ui_width.trace_radio_button.isChecked():
		ax2 = ax1.twinx()
		ax2.plot(range(-40,41,2),la2[1,:],'b-')
		ax2.set_ylabel('trace angle', color='b')
		ax2.tick_params('y', colors='b')
		
	if ui_width.thickness_checkBox.isChecked():
		t=np.float(ui_width.thickness.text())
		d=t/np.sqrt(1-np.dot(nr,B)**2)
		ax1.plot(range(-40,41,2),la2[0,:]*d,'r-')
		ax1.set_ylabel('w (nm)', color='black')
	else:
		ax1.plot(range(-40,41,2),la2[0,:],'r-')
		ax1.set_ylabel('w/d', color='black')
	ax1.figure.canvas.draw()  
	
def clear_width():
	ax1 = figure_width.add_subplot(111)
	ax1.figure.clf()
	ax1.figure.canvas.draw()  
	
####################################################
#
# Intersections
#
#######################################################

def intersect_norm(n1,n2,d):
	global Dstar, D, M
	Dr=1e10*D
	Dstarr=1e-10*Dstar
	n1=n1/np.linalg.norm(n1)
	n1=np.dot(Dstarr,n1)
	
	if d==0:
		l=ui_inter.checkBox.isChecked()
		n2=n2/np.linalg.norm(n2)
		n2=np.dot(Dstarr,n2)
	else:
		l=ui_inter.checkBox_2.isChecked()
		n2=np.dot(np.linalg.inv(M), n2)

	n=np.cross(n1,n2)	
	if l:
		n=np.dot(np.linalg.inv(Dr),n)
		if var_hexa()==1:
	            na=(2*n[0]-n[1])/3
		    n2a=(2*n[1]-n[0])/3
		    n[0]=na
		    n[1]=n2a
	else:
		n=np.dot(np.linalg.inv(Dstarr),n)
	return n
	

def intersections_plans():
	n1_plan=ui_inter.n1_entry.text().split(",")
	n1=np.array([np.float( n1_plan[0]),np.float(n1_plan[1]),np.float(n1_plan[2])])
	n2_plan=ui_inter.n2_entry.text().split(",")
	n2=np.array([np.float( n2_plan[0]),np.float(n2_plan[1]),np.float(n2_plan[2])])
	n=intersect_norm(n1,n2,0)
	ui_inter.n1n2_label.setText(str(np.round(100*n[0],decimals=3))+', '+str(np.round(100*n[1],decimals=3))+', '+str(np.round(100*n[2],decimals=3)))
	           
def intersection_dir_proj():
	global M
	n_proj=ui_inter.n_proj_entry.text().split(",")
	n=np.array([np.float( n_proj[0]),np.float(n_proj[1]),np.float(n_proj[2])])
	angle=np.float(ui_inter.angle_proj_entry.text())*np.pi/180
	norm_xyz=np.array([np.cos(angle),-np.sin(angle),0])
	n_intersect=intersect_norm(n,norm_xyz,1)
	ui_inter.n_proj_label.setText(str(np.round(100*n_intersect[0],decimals=3))+', '+str(np.round(100*n_intersect[1],decimals=3))+', '+str(np.round(100*n_intersect[2],decimals=3)))
		
def intersection_cone():
	global Dstar,D
	Dr=1e10*D
	Dstarr=1e-10*Dstar
	n_c=ui_inter.n_cone_entry.text().split(",")
	n=np.array([np.float( n_c[0]),np.float(n_c[1]),np.float(n_c[2])])
	c_c=ui_inter.cone_entry.text().split(",")
	c=np.array([np.float( c_c[0]),np.float(c_c[1]),np.float(c_c[2])])
	r=np.cos(np.float(ui_inter.cone_angle_entry.text())*np.pi/180)
	n=np.dot(Dstarr,n)
	n=n/np.linalg.norm(n)
	c=np.dot(Dstarr,c)
	c=c/np.linalg.norm(c)
	
	x1=(c[0]*n[1]**2*r + c[0]*n[2]**2*r - c[1]*n[0]*n[1]*r - c[1]*n[2]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2) - c[2]*n[0]*n[2]*r + c[2]*n[1]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2))/(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2)
	y1=(-c[0]*n[0]*n[1]*r + c[0]*n[2]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2) + c[1]*n[0]**2*r + c[1]*n[2]**2*r - c[2]*n[0]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2) - c[2]*n[1]*n[2]*r)/(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2)
	z1=(-r*(c[0]*n[0]*n[2] + c[1]*n[1]*n[2] - c[2]*n[0]**2 - c[2]*n[1]**2) + (-c[0]*n[1] + c[1]*n[0])*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2))/(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2)
	x2=(c[0]*n[1]**2*r + c[0]*n[2]**2*r - c[1]*n[0]*n[1]*r + c[1]*n[2]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2) - c[2]*n[0]*n[2]*r - c[2]*n[1]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2))/(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2)
	y2=(-c[0]*n[0]*n[1]*r - c[0]*n[2]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2) + c[1]*n[0]**2*r + c[1]*n[2]**2*r + c[2]*n[0]*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2) - c[2]*n[1]*n[2]*r)/(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2)
	z2=(-r*(c[0]*n[0]*n[2] + c[1]*n[1]*n[2] - c[2]*n[0]**2 - c[2]*n[1]**2) + (c[0]*n[1] - c[1]*n[0])*np.sqrt(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2 - n[0]**2*r**2 - n[1]**2*r**2 - n[2]**2*r**2))/(c[0]**2*n[1]**2 + c[0]**2*n[2]**2 - 2*c[0]*c[1]*n[0]*n[1] - 2*c[0]*c[2]*n[0]*n[2] + c[1]**2*n[0]**2 + c[1]**2*n[2]**2 - 2*c[1]*c[2]*n[1]*n[2] + c[2]**2*n[0]**2 + c[2]**2*n[1]**2)
	
	r1=np.array([x1,y1,z1])
	r2=np.array([x2,y2,z2])
	
	if ui_inter.checkBox_3.isChecked():
		r1=np.dot(np.linalg.inv(Dr),r1)
		r2=np.dot(np.linalg.inv(Dr),r2)
		if var_hexa()==1:
	            na=(2*r1[0]-r1[1])/3
		    n2a=(2*r1[1]-r1[0])/3
		    r1[0]=na
		    r1[1]=n2a
		    na2=(2*r2[0]-r2[1])/3
		    n2a2=(2*r2[1]-r2[0])/3
		    r2[0]=na2
		    r2[1]=n2a2
	else:
		r1=np.dot(np.linalg.inv(Dstarr),r1)
		r2=np.dot(np.linalg.inv(Dstarr),r2)
	
	ui_inter.cone_plane_label.setText(str(np.round(100*r1[0], decimals=3))+','+str(np.round(100*r1[1], decimals=3))+','+str(np.round(100*r1[2], decimals=3))+'\n'+str(np.round(100*r2[0], decimals=3))+','+str(np.round(100*r2[1], decimals=3))+','+str(np.round(100*r2[2], decimals=3)) )
	

###################################################
#
# Plot Kikuchi bands  / Diffraction pattern
# The diff spots/Kikuchi bands are computed within the kinematical approximation, owing the structure factor and scattering factors. 
# indicated in the corresponding txt files. The scattering factor is computed for every elements according to 
# a sum of Gaussian functions (see http://lampx.tugraz.at/~hadley/ss1/crystaldiffraction/atomicformfactors/formfactors.php)
#
#################################################
def diff_reciprocal():
	global axesh_diff,axes_diff,G,V,Dstar
	
	e=np.int(ui_kikuchi.indices_entry.text())
	axes_diff=np.zeros(((2*e+1)**3-1,3))
    	axesh_diff=np.zeros(((2*e+1)**3-1,4))
	id=0
	for i in range(-e,e+1):
		for j in range(-e,e+1):
	    		for k in range(-e,e+1):
				if (i,j,k)!=(0,0,0):
					Ma=np.dot(Dstar,np.array([i,j,k],float))
					axesh_diff[id,0:3]=Ma/np.linalg.norm(Ma)
					if ui_kikuchi.diff_radioButton.isChecked():
				    		axesh_diff[id,3]=extinction(ui.space_group_Box.currentText(),i,j,k,10000,1)[0]
				    		axes_diff[id,:]=np.array([i,j,k])
						
					if ui_kikuchi.kikuchi_radioButton.isChecked():
							m=reduce(lambda x,y:GCD(x,y),[i,j,k])
							if (np.around(i/m)==i/m) & (np.around(j/m)==j/m) & (np.around(k/m)==k/m):
								axes_diff[id,:]=np.array([i,j,k])/m
							else:
								axes_diff[id,:]=np.array([i,j,k])
			    				axesh_diff[id,3]
				    	id=id+1
						
	axesh_diff=axesh_diff[~np.all(axesh_diff[:,0:3]==0, axis=1)]
    	axes_diff=axes_diff[~np.all(axes_diff==0, axis=1)]
    	
    	for z in range(0, np.shape(axes_diff)[0]):
		I,h,k,l=extinction(ui.space_group_Box.currentText(),axes_diff[z,0],axes_diff[z,1],axes_diff[z,2],e,0)
		
		if I>0:
        	        axesh_diff[z,3]=I
        	        axes_diff[z,:]=np.array([h,k,l])
		else:
			axesh_diff[z,0:3]=np.array([0,0,0])
			axesh_diff[z,3]=1
        	        axes_diff[z,:]=np.array([0,0,0])
        axesh_diff=axesh_diff[~np.all(axesh_diff[:,0:3]==0, axis=1)]
    	axes_diff=axes_diff[~np.all(axes_diff==0, axis=1)]
    	
	
	return axes_diff, axesh_diff

def set_diff_cond():
	ui_kikuchi.t_entry.setText('100')
	ui_kikuchi.indices_entry.setText('5')
	ui_kikuchi.angle_entry.setText('3')
	ui_kikuchi.spot_size_entry.setText('100')
	ui_kikuchi.error_entry.setText('1')

def set_kikuchi_cond():
	ui_kikuchi.t_entry.setText(' ')
	ui_kikuchi.indices_entry.setText('3')
	ui_kikuchi.angle_entry.setText('15')
	ui_kikuchi.spot_size_entry.setText(' ')
	ui_kikuchi.error_entry.setText(' ')

	
def plot_kikuchi():
	global M,G,V,axesh_diff,axes_diff
		
	a_k = figure_kikuchi.add_subplot(111)
	a_k.clear()
	a_k = figure_kikuchi.add_subplot(111)
    	E=np.float(ui_kikuchi.E_entry.text())
    	lamb=6.6e-34/np.sqrt(2*9.1e-31*1.6e-19*E*1e3*(1+1.6e-19*E*1e3/2/9.31e-31/9e16))
    	ang=np.float(ui_kikuchi.angle_entry.text())*np.pi/180
	ap=np.sin(ang)/(1+np.cos(ang))
	lim=np.tan(ang)/lamb*1e-9
	m=np.max(axesh_diff[:,3])

	
	if ui_kikuchi.diff_radioButton.isChecked():
		smax=np.float(ui_kikuchi.error_entry.text())*1e9
		ang_max=np.arccos(1-lamb*smax)
		thick=np.float(ui_kikuchi.t_entry.text())*1e-9
		for t in range(0,np.shape(axesh_diff)[0]):
			T=np.dot(M,axesh_diff[t,0:3])
			if np.abs(T[2])<np.sin(ang_max):
				Fg=np.sqrt(axesh_diff[t,3])*1e-10
				d=1/(np.sqrt(np.dot(axes_diff[t,:],np.dot(np.linalg.inv(G),axes_diff[t,:]))))
				tb=np.arcsin(lamb/2/d)*180/np.pi
				S=(np.dot(Rot(2*tb,-T[1],T[0],0),np.array([0,0,1]))-np.array([0,0,1]))/lamb-T/d
				s=np.linalg.norm(S)
				xi=np.pi*V*np.cos(tb*np.pi/180)/lamb/Fg
				se=np.sqrt(s**2+1/xi**2)
				I=(thick*np.pi/xi)**2*np.sinc(se*thick)**2
				st=str(int(axes_diff[t,0]))+','+str(int(axes_diff[t,1]))+','+str(int(axes_diff[t,2]))
		    		if ui_kikuchi.label_checkBox.isChecked():
		    			a_k.annotate(st,(T[0]/d*1e-9,T[1]/d*1e-9), color="white")
				a_k.scatter(T[0]/d*1e-9,T[1]/d*1e-9,s=I*np.float(ui_kikuchi.spot_size_entry.text()), color="white")
				a_k.plot(0,0,'w+')
				a_k.axis('equal')
				a_k.axis([-lim,lim,-lim,lim])
				a_k.axis('off')
				
				
	if ui_kikuchi.kikuchi_radioButton.isChecked():
		for t in range(0,np.shape(axesh_diff)[0]):
				T=np.dot(M,axesh_diff[t,0:3])
				if np.abs(T[2])<np.sin(ang):
					r=np.sqrt(T[0]**2+T[1]**2+T[2]**2)
					A=np.zeros((2,50))
					B=np.zeros((2,50))
					Qa=np.zeros((1,2))
					Qb=np.zeros((1,2))
					th=np.arctan2(T[1],T[0])*180/np.pi
					w=0
					ph=np.arccos(T[2]/r)*180/np.pi
					d=1/(np.sqrt(np.dot(axes_diff[t,:],np.dot(np.linalg.inv(G),axes_diff[t,:]))))
					tb=np.arcsin(lamb/2/d)*180/np.pi/2
					
					for g in np.linspace(-np.pi/2,np.pi/2,50):
		    				Aa=np.dot(Rot(th,0,0,1),np.dot(Rot(ph-tb,0,1,0),np.array([np.sin(g),np.cos(g),0])))
		    				Ab=np.dot(Rot(th,0,0,1),np.dot(Rot(ph+tb,0,1,0),np.array([np.sin(g),np.cos(g),0])))
		    				A[:,w]=proj_gnomonic(Aa[0],Aa[1],Aa[2])*300
		    				B[:,w]=proj_gnomonic(Ab[0],Ab[1],Ab[2])*300
		    				Qa=np.vstack((Qa,A[:,w]))
		    				Qb=np.vstack((Qb,B[:,w]))
		    			w=w+1
		    			Qa=np.delete(Qa,0,0)
		    			Qb=np.delete(Qb,0,0)
		    			
		    			st=str(int(axes_diff[t,0]))+','+str(int(axes_diff[t,1]))+','+str(int(axes_diff[t,2]))
		    			if ui_kikuchi.label_checkBox.isChecked():
		    				a_k.annotate(st,(Qa[2,0]+300,Qa[2,1]+300),ha='center', va='center',rotation=th-90, color="white")
		    			
					a_k.plot(Qa[:,0]+300,Qa[:,1]+300,'w-', linewidth=axesh_diff[t,3]/m)
					a_k.plot(Qb[:,0]+300,Qb[:,1]+300,'w-', linewidth=axesh_diff[t,3]/m)
					a_k.plot(300,300,'wo')
					a_k.set_facecolor('black')
					a_k.axis('equal')
					a_k.axis([300*(1-ap),300*(1+ap),300*(1-ap),300*(1+ap)])
					
			
	a_k.figure.canvas.draw() 
	
 	

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

# Read space_group file
	f_space=open(os.path.join(os.path.dirname(__file__), 'space_group.txt'),"r")

	x_space=[]

	for line in f_space:
	    x_space.append(map(str, line.split()))
	    
	
	ui.space_group_Box.addItems(" ")
	for i in range(0,len(x_space)):
	    if len(x_space[i])==1:
		ui.space_group_Box.addItems(x_space[i])
		
	f_space.close()
	
# Read scattering factor file
	f_scatt=open(os.path.join(os.path.dirname(__file__), 'scattering.txt'),"r")

	x_scatt=[]

	for line in f_scatt:
	    x_scatt.append(map(str, line.split()))
	    
		
	f_scatt.close()		
	
# Ctrl+z shortcut to remove clicked pole

	shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+z"), Index)
        shortcut.activated.connect(undo_click_a_pole)

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
	
	Hkl_uvw=QtGui.QDialog()
	ui_hkl_uvw=hkl_uvwUI.Ui_hkl_uvw()
	ui_hkl_uvw.setupUi(Hkl_uvw)
	Index.connect(ui.actionHkl_uvw, QtCore.SIGNAL('triggered()'),Hkl_uvw.show)
	ui_hkl_uvw.pushButton_to_uvw.clicked.connect(to_uvw)
	ui_hkl_uvw.pushButton_to_hkl.clicked.connect(to_hkl)
	
	
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
	ui_width.clear_button.clicked.connect(clear_width)
	figure_width=plt.figure()
	canvas_width=FigureCanvas(figure_width)
	ui_width.mplvl.addWidget(canvas_width)
	toolbar_width = NavigationToolbar(canvas_width, canvas_width)
	toolbar_width.setMinimumWidth(601)
	
	Intersections = QtGui.QDialog()
	ui_inter=intersectionsUI.Ui_Intersections()
	ui_inter.setupUi(Intersections)
	Index.connect(ui.actionCalculate_intersections, QtCore.SIGNAL('triggered()'), Intersections.show) 
	ui_inter.pushButton_intersections_plans.clicked.connect(intersections_plans)            
	ui_inter.pushButton_intersection_proj.clicked.connect(intersection_dir_proj)
	ui_inter.pushButton_intersection_cone.clicked.connect(intersection_cone)
	
	Kikuchi=QtGui.QDialog()
	ui_kikuchi=kikuchiUI.Ui_Kikuchi()
	ui_kikuchi.setupUi(Kikuchi)
	Index.connect(ui.actionPlot_Kikuchi_lines, QtCore.SIGNAL('triggered()'), Kikuchi.show) 
	ui_kikuchi.buttonBox.rejected.connect(Kikuchi.close)
	ui_kikuchi.buttonBox.accepted.connect(plot_kikuchi)
	ui_kikuchi.Diff_button.clicked.connect(diff_reciprocal)
	ui_kikuchi.diff_radioButton.clicked.connect(set_diff_cond)
	ui_kikuchi.kikuchi_radioButton.clicked.connect(set_kikuchi_cond)	
	ui_kikuchi.E_entry.setText('200')
	figure_kikuchi=plt.figure()
	figure_kikuchi.patch.set_facecolor('black')
	canvas_kikuchi=FigureCanvas(figure_kikuchi)
	ui_kikuchi.mplvl.addWidget(canvas_kikuchi)
	toolbar_kikuchi = NavigationToolbar(canvas_kikuchi, canvas_kikuchi)
	toolbar_kikuchi.setMinimumWidth(100)
	toolbar_kikuchi.setStyleSheet("background-color:White;")

	
	ui.button_trace2.clicked.connect(princ2)
	ui.button_trace.clicked.connect(princ)
	ui.reciprocal_checkBox.stateChanged.connect(lattice_reciprocal)
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
	
	var_lock=0
	ui.lock_checkButton.setChecked(False)
	ui.color_trace_bleu.setChecked(True)
	ui.wulff_button.setChecked(True)
	ui.wulff_button.setChecked(True)
	ui.d_label_var.setText('0')
	ui.text_size_entry.setText('12')
	mpl.rcParams['font.size'] = ui.text_size_entry.text()
	ui.abc_entry.setText('1,1,1')
	ui.alphabetagamma_entry.setText('90,90,90')
	ui.phi1phiphi2_entry.setText('0,0,0')
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
	ui.tilt_angle_entry.setText('0')	
	ui.image_angle_entry.setText('0')
	ui.d_entry.setText('1')
	ui.rot_g_entry.setText('5')
	ui.inclination_entry.setText('30')
	a = figure.add_subplot(111)
	tilt_axes()
	wulff()
	Index.show()
	sys.exit(app.exec_())




