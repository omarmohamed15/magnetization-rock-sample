'''
License

This code is licensed under under the [BSD 3-clause]
(http://choosealicense.com/licenses/bsd-3-clause/) license. 
See the file `LICENSE.md`
'''

import numpy as np
from fatiando import mesher, gridder
from fatiando.gravmag import prism, sphere, polyprism
from fatiando.utils import ang2vec, vec2ang
from fatiando.vis import mpl
from fatiando.constants import CM, T2NT

def point2grid(x, y, effective_area, ns, z = None):
    '''
    Creates a regular grid of Qx x Qy points
    over the effective_area centered at each point
    (x,y).
    
    input
    x: numpy array 1D - x coordinates of the points (in meters).
    y: numpy array 1D - y coordinates of the points (in meters).
    effective_area: tuple - x and y dimensions (in microns) of the area.
    ns: int - number of points along the x- and y-axis.
    y: numpy array 1D - y coordinates of the points (in meters) - default is None.
    
    output
    
    xgrid: numpy array 1D - x coordinates of the grid (in meters).
    ygrid: numpy array 1D - y coordinates of the grid (in meters).
    zgrid: numpy array 1D - z coordinates of the grid (in meters).
    '''
    
    assert (effective_area[0] > 0) and (effective_area[1] > 0), \
    'effective area must be positive'
        
    assert x.size == y.size, 'x and y must have the same number of elements'
    
    if z is not None:
        assert x.size == z.size, 'x, y and z must have the same number of elements'
    
    assert ns%2 != 0, 'ns must be odd'
        
    dx = 0.000001*effective_area[0]/ns
    dy = 0.000001*effective_area[1]/ns
    
    ns2 = int(ns//2)
    Q = int(ns*ns)
    
    x_small_grid, y_small_grid = np.meshgrid(dx*np.arange(-ns2, ns2+1), dy*np.arange(-ns2, ns2+1))
    
    #print x_small_grid
    #print y_small_grid
    
    xgrid = np.resize(x, Q*x.size).reshape(Q,x.size).T.ravel()
    ygrid = np.resize(y, Q*y.size).reshape(Q,y.size).T.ravel()
    
    if z is not None:
        zgrid = np.resize(z, Q*z.size).reshape(Q,z.size).T.ravel()
    
    for i, xi in enumerate(x):
        xgrid[i*Q:(i+1)*Q] += x_small_grid.ravel()
    for i, yi in enumerate(y):
        ygrid[i*Q:(i+1)*Q] += y_small_grid.ravel()
        
    if z is not None:
        return xgrid, ygrid, zgrid
    else:
        return xgrid, ygrid

def magnetic_data(x, y, z, model, alpha, eff_area = None, grains = None):
    '''
    Calculates the magnetic indution on the plane alpha
    located around the sample.
    
    input
    
    x, y, z: numpy arrays - Cartesian coordinates (in m) of 
             the points on which the magnetic field is calculated.
    model: list - geometrical elements of the Fatiando a Terra 
           class mesher - interpretation model.
    grains: None or list - if not None, is a list of geometrical elements 
            of the Fatiando a Terra class mesher - randomly magnetized grains.
    alpha: int - index of the plane on which the data are calculated.
    eff_area: None or tuple of floats - effective area of the simulated sensor.
              If None, calculates the field at the points x, y, z.
              If not None, eff_area = (lx, ly), where lx and ly
              are the side lengths (in microns) of the effective area of the sensor
              along the x and y axes.
    ns: None or tuple of ints - number of points on which the field is
        averaged within the effective area of the sensor.
        Is None if eff_area is none.
        If effe_area is not None, ns = (nsx,nsy), where nsx and nsy are
        the number of points on which the filed is averaged within the
        the effective area of the sensor along the x and y axes.
    
    output
    
    B: numpy array - magnetic data
    '''
    
    assert (alpha == 0) or (alpha == 1) or (alpha == 2) or (alpha == 3), \
           'alpha must be equal to 0, 1, 2 or 3'
           
    if eff_area is not None:
        
        ns = 7
        
        xg, yg, zg = point2grid(x, y, eff_area, ns, z)
            
        if (alpha == 0) or (alpha == 2):
            B = np.mean(np.reshape(prism.bz(xg, yg, zg, model), (x.size, ns*ns)), axis=1)
            if grains is not None:
                B += np.mean(np.reshape(sphere.bz(xg, yg, zg, grains), (x.size, ns*ns)), axis=1)

        if (alpha == 1) or (alpha == 3):
            B = np.mean(np.reshape(prism.by(xg, yg, zg, model), (x.size, ns*ns)), axis=1)
            if grains is not None:
                B += np.mean(np.reshape(sphere.by(xg, yg, zg, grains), (x.size, ns*ns)), axis=1)
        
    else:
        if (alpha == 0) or (alpha == 2):
            B = prism.bz(x, y, z, model)
            if grains is not None:
                B += sphere.bz(x, y, z, grains)
        if (alpha == 1) or (alpha == 3):
            B = prism.by(x, y, z, model)
            if grains is not None:
                B += sphere.by(x, y, z, grains)

    return B

def sample(Lx,Ly,Lz,P,m=None,inc=None,dec=None):
    '''
    Define the interpretation model as a 1D array of rectangular prisms
    along the x-axis.
    
    input
    
    Lx: float - side length of all prisms along x (m).
    
    Ly: float - side length of all prisms along x (m).
    
    Lz: float - side length of all prisms along x (m).
    
    P: int - number of prisms
    
    m: list - magnetization intensity (A/m) of each prism.
    inc: list - magnetization inclination (graus) of each prism.
    dec: list - magnetization declination (graus) of each prism.
    
    output
    
    model: list of geometrical elements mesher class of the 
        Fatiando a Terra package - interpretation model.
    '''
    
    sizex = Lx
    sizey = Ly
    sizez = Lz

    L = P*sizex
    a = -0.5*L
    
    model = []

    if ((m is not None) & (inc is not None) & (dec is not None)):
        intensity = np.array(m)
        inclinacao = np.array(inc)
        declinacao = np.array(dec)
        mag = []
        for i in range(P):
            mag.append(ang2vec(intensity[i],inclinacao[i],declinacao[i]))
    
        for i in range(P):
            model.append(mesher.Prism(a+i*sizex, a+(i+1)*sizex, \
                                      -0.5*sizey, 0.5*sizey, \
                                      -0.5*sizez, 0.5*sizez, \
                                      {'magnetization': mag[i]}))
    else:
        for i in range(P):
            model.append(mesher.Prism(a+i*sizex, a+(i+1)*sizex, \
                                      -0.5*sizey, 0.5*sizey, \
                                      -0.5*sizez, 0.5*sizez))
        
    return model



def sensitivity(P,x,y,z,model,alpha, eff_area = None):
    '''
    Calculates the Jacobian matrix of the inversion
    
    input
    
    P: int - number of prisms
    
    x: list - coordinates x (in meters)
    
    y: list - coordinates y (in meters)
    
    z: list - coordinates z (in meters)
    model: list - Geometrical elements of the mesher class
        of the Fatiando a Terra package - interpretation model.
    
    G: matrix with number of rows equal to the number N of data and 
       number of colunms equal to the number M of parameters.
        
    '''
    
    G = np.empty((x.size, 3*P))
    
    cols = np.reshape(np.arange(3*P), (P, 3))
    
    if eff_area is not None:
    
        ns = 7
        Q = ns*ns
        
        xg, yg, zg = point2grid(x, y, eff_area, ns, z)
        
        for i, col in enumerate(cols):
            if (alpha == 0 or alpha == 2):
                G[:,col[0]] = np.mean(np.reshape(prism.kernelxz(xg, yg, zg, model[i]), (x.size, Q)), axis=1)
                G[:,col[1]] = np.mean(np.reshape(prism.kernelyz(xg, yg, zg, model[i]), (x.size, Q)), axis=1)
                G[:,col[2]] = np.mean(np.reshape(prism.kernelzz(xg, yg, zg, model[i]), (x.size, Q)), axis=1)
            if (alpha == 1 or alpha == 3):
                G[:,col[0]] = np.mean(np.reshape(prism.kernelxy(xg, yg, zg, model[i]), (x.size, Q)), axis=1)
                G[:,col[1]] = np.mean(np.reshape(prism.kernelyy(xg, yg, zg, model[i]), (x.size, Q)), axis=1)
                G[:,col[2]] = np.mean(np.reshape(prism.kernelyz(xg, yg, zg, model[i]), (x.size, Q)), axis=1)
                
    else:
        for i, col in enumerate(cols):
            if (alpha == 0 or alpha == 2):
                G[:,col[0]] = prism.kernelxz(x, y, z, model[i])
                G[:,col[1]] = prism.kernelyz(x, y, z, model[i])
                G[:,col[2]] = prism.kernelzz(x, y, z, model[i])
            if (alpha == 1 or alpha == 3):
                G[:,col[0]] = prism.kernelxy(x, y, z, model[i])
                G[:,col[1]] = prism.kernelyy(x, y, z, model[i])
                G[:,col[2]] = prism.kernelyz(x, y, z, model[i])
    
    G *= CM*T2NT
    return G

def parameters_sph(N,coord):
    '''
    Makes the transformation from Cartesian Coordinates to Intensity, Declination
    and Inclination
    
    input
    
    N: int - number of prisms
    
    coord: list - list of Cartesian Coordinates of the parameters
    
    return
    
    mag_sph: array - Matrix with shape (N x 3) containing each row with the values of 
    intensity, declination and inclination.
    '''
    
    mag_cart = []
    for i in range(N):
        mag_cart.append(np.array([coord[3*i],coord[3*i+1],coord[3*i+2]]))
        
        
    mag_spheric = []
    for i in range(N):
        aux = vec2ang(mag_cart[i])
        if (aux[2] > 180.):
            aux[2] -= 360.
        if (aux[2] <= -180.):
            aux[2] += 360.
        mag_spheric.append(aux)
    mag_sph = np.array(mag_spheric)
    return mag_sph



def proj_polar(N,mag,color='k',simbolo='o',size=10):
    
    '''
    Generates a figure of a polar projection of estimates
    
    input
    
    N: int - number of prisms
    
    mag: array - Matrix with shape (N x 3) containing intensity, declination and inclination
    
    proj: array - list of projection values
    
    return
    
    Figure with polar projections of the estimates
    
    '''
       
    projections = []
    for i in range(N):
        projections.append(np.sqrt((np.cos(np.deg2rad(mag[i,1]))*np.cos(np.deg2rad(mag[i,2])))**2 +(np.cos(np.deg2rad(mag[i,1]))*np.sin(np.deg2rad(mag[i,2])))**2))
        proj = np.array(projections)
    for i in range(N):
        if mag[i,1] >= 0.0:
            mpl.plot(np.deg2rad(mag[i,2]), proj[i], marker=simbolo, ms=size,mec= color, mew=3, mfc= color, fillstyle='full')
        else:
            mpl.plot(np.deg2rad(mag[i,2]), proj[i], marker=simbolo, ms=size, mec= color, mew=3, fillstyle='none') 



def dipolesrand(N, seed,n,deg_dec,deg_inc,std,mag,raio,Lx,Ly,Lz):
    '''
    Generates a set of spheres randomly distribuited within the model
    
    input
    
    N: int - number of prisms
        
    s: int - seed value
    
    n: int - number of magnetized spheres
    
    deg_dec: float - mean value of the declination (degrees)
    
    deg_inc: float - mean value of inclination (degrees)
    
    std: float - standard deviation of the declination and inclination (degrees)
    
    mag: float - magnetization intensity of each sphere (A/m)
    
    raio: float - radius of each sphere (m)  
    
    Lx,Ly,Lz: int - prisms dimensions (m)
    
    return
    
    modelrand: list of geometrical objects using the library Fatiando a Terra.
    '''
    np.random.seed(seed=seed)
    sizex = Lx
    sizey = Ly
    sizez = Lz
    L = N*sizex
    R = raio
    Coordx = np.random.uniform(-0.5*L+R,+0.5*L-R,n) 
    Coordy = np.random.uniform(-0.5*sizey+R,+0.5*sizey-R,n) 
    Coordz = np.random.uniform(-0.5*sizez+R,+0.5*sizez-R,n)
    Dec_rand = np.random.normal(deg_dec, std,n)
    Inc_rand = np.random.normal(deg_inc, std,n)
    
    magrand = []
    for i in range(n):
        magrand.append(ang2vec(mag,Inc_rand[i],Dec_rand[i]))
    
    modelrand = []
    for i in range(n):
        modelrand.append(mesher.Sphere(Coordx[i], Coordy[i], Coordz[i], R , {'magnetization': magrand[i]})) 

    return modelrand,Coordx,Coordy,Coordz

def residual(do,dp):
    '''
    Calculates the residuals
    
    input
    
    do : numpy array - vector containing the observables
    
    dp : numpy array - vector containing the predicted data

    output

    r_norm : numpy array - residual normalized
    
    r_mean : float - mean of the residuals

    r_std : float - standard deviation of the residuals
    '''
    r = do - dp
    r_mean = np.mean(r)
    r_std = np.std(r)
    r_norm = (r - r_mean)/r_std
    return r_norm, r_mean, r_std
   
def coordplane(h,L,Nx,Ny,area,alpha,theta):
    '''
    Generates the Coodinates of observation
    
    input
    
    h: int - distance (10**-6 m) sensor-to-sample
    
    L: float - side length of the sample (in mm) along the x-axis
    
    Nx: int - number of observations along the x-axis
    
    Ny: int - number of observations along the y-axis
    
    area: list - limit boundaries of the observation planes
    
    alpha: int - number of the observation plane
    
    theta: int - angle (in radians) of the rotation
    
    return
    
    x,y,z: coordinates of the observations
    
    '''
    
    shape = (Nx, Ny)
    areaxy = area
    dist = h*0.000001
    size = L
    voo = dist + 0.5*size
    ang = np.deg2rad(theta)
    cos = np.cos(ang)
    sin = np.sin(ang)
    
    if (alpha == 0):
        x, y, z = gridder.regular(areaxy, shape, -voo)
    if (alpha == 1):
        x, z, y = gridder.regular(areaxy, shape, voo)
    if (alpha == 2):
        x, y, z = gridder.regular(areaxy, shape, voo)
    if (alpha == 3):
        x, z, y = gridder.regular(areaxy, shape, -voo)
    
    x_rot = []
    y_rot = []
    z_rot = []
    if (alpha==0 or alpha ==2):
        x_rot.append(cos*x - sin*y)
        y_rot.append(sin*x + cos*y)
        z_rot.append(z)
    if (alpha == 1 or alpha == 3):
        x_rot.append(cos*x - sin*z)
        z_rot.append(sin*x + cos*z)
        y_rot.append(y)
    
    return x_rot[0], y_rot[0], z_rot[0]