# -*- coding: utf-8 -*-
"""
Created on Wed Sep 21 14:23:09 2016
@authors: Anders Hansson, Tuong Lam, Bernhard Pöchtrager, Annika Stegie
"""
from  scipy import *
from  pylab import *
import numpy as np
import warnings

class OptimizationMethods:
    #define constants for conditions on the inexact line search (Wolfe-Powell-Parameter)
    ALPHAL=0;
    ALPHAU=math.pow(10,99);
    
    # several line search methods possible
        # for example again a Newton Method, Bisection, Steepest descent
        
        # Bisection - discard it because it is really hard to get a good initial guess
        # and it is slow
        # actually not such a nice method because the sign-change has to be detected
        # evalute f at different points around xk to detect sign change
        # leftEnd = #nearest point to the left of sign change
        # rightEnd = #nearest point to the right of sign change
        # a starting alpha is needed, maybe take 1?
        # have to find min of fAlpha, root of gAlpha
#        gAlpha = g(xk+alpha*sk)
#        alpha = (rightEnd-leftEnd)/2       
#        while gAlpha > tol:
#            if gAlpha == 0:
#                return alpha
#            elif gAlpha*f(xk+leftEnd*sk) < 0:
#                rightEnd = alpha
#            else :
#                leftEnd = alpha
#            alpha = (rightEnd-leftEnd)/2
#            gAlpha = g(xk+alpha*sk)
#            # it shoukd be checked if this is really a min or any other stationary point
#            if (g(xk+(alpha+0.5e-5)*sk)-g(xk+(alpha-0.5e-5)*sk))/1e-5 <= 0:
#                #what should be done here?
#        return alpha
    def lineSearchExactSteepestDesent(self,xk,sk,alpha=1,beta=.5,gamma=1e-2):
        """
        Method to calculate the stepsize in a Quasi-Newton method by the
        steepest descent algorithm.
        This function just needs the parameter xk, sk and optionally alpha.
        alpha = 1 is the default initial guess to start the algorithm.
        The rest of the parameters is not changed!
        :return: alpha
        """
        # Steepest descent method
        while g(xk+alpha*sk) > tol:
            # stepsize calculated by Armijo's method              
            exponent = 1
            stepsize = 1
            while f(xk+alpha*sk-stepsize*g(xk+alpha*sk))-f(xk+alpha*sk) <= -stepsize*gamma*norm(g(alpha*xk))**2:
                stepsize = beta**exponent
                exponent = exponent+1
            alpha=alpha-stepsize*g(alpha*xk)
        # check if really min or just stationary point  
        if (g(xk+(alpha+0.5e-5)*sk)-g(xk+(alpha-0.5e-5)*sk))/1e-5 <= 0:
            warnings.warn("lineSearchExactSteepestDesent: The found stationary point alpha might not be a real minimum of the stepsize.")
        return alpha
        
    def lineSearchExactNewton(self,x,sk,alpha0=1):
        """
        Method to do linesearch by classical Newton method.
        This function just needs the parameter x, alpha0 and s.
        The rest of the parameters are not used in this function!
        Default initial guess for alpha is 1.
        :return: returns alpha
        """        
        # Newton Method
        def fAlpha(alpha):
            return self.optProb.f(x+alpha*sk)
        def gAlpha(alpha):
            return self.optProb.g(x+alpha*sk)*sk
        optProbAlpha=OptimizationProblem(fAlpha,gAlpha)
        #fAlpha function and gradient must be put in; no line search, finite difference approx of H
        CN = QuasiNewton(optProbAlpha,self.finiteDifference,True)
        return CN.solve(1.)  #choose any number

    def lineSearchInexact(self,x,s,alpha0=1,rho=0.1,sigma=0.7,tau=0.1,chi=9):
        """
        doing inexact linesearch with Wolfe-Powell condition and the parameters
        given above
        :return: returns alpha (the solution of the linesearch algorithm)
        and the value f(x+alpha*s)
        """
        alphaU=self.ALPHAU
        alphaL=self.ALPHAL
        fAlpha0=self.optProb.f(x+alpha0*s);
        fAlphaL=self.optProb.f(x+alphaL*s);
        gAlpha0=self.optProb.g(x+alpha0*s);
        gAlphaL=self.optProb.g(x+alphaL*s);
        boolLC=self.lc(alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho,sigma)
        boolRC=self.rc(alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho)
        while (boolLC and boolRC)==False:
            if boolLC:
                #case !boolLC==False (block 2)
                alphaU=min([alpha0,alphaU])
                #do interpolation (book Antoniou - formula 4.57)
                denom=2*(fAlphaL-fAlpha0+(alpha0-alphaL)*gAlphaL)
                alpha0Temp=math.pow(alpha0-alphaL,2)*gAlphaL/denom
                alpha0Temp=max([alpha0Temp,alphaL+tau(alphaU-alphaL)])
                alpha0=min([alpha0Temp,alphaU-tau(alphaU-alphaL)])
            else:
                #case !boolLC==True (block 1)
                #do extrapolationpolation (book Antoniou - formula 4.58)
                alpha0Temp=(alpha0-alphaL)*gAlpha0/(gAlphaL-gAlpha0)
                alpha0Temp=max([alpha0Temp,alphaL+tau(alphaU-alphaL)])
                alphaL=alpha0
                alpha0=alpha0+min([alpha0Temp,alphaU-tau(alphaU-alphaL)])
            fAlpha0=self.optProb.f(x+alpha0*s);
            fAlphaL=self.optProb.f(x+alphaL*s);
            gAlpha0=self.optProb.g(x+alpha0*s);
            gAlphaL=self.optProb.g(x+alphaL*s);
            boolLC=self.lc(alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho,sigma)
            boolRC=self.rc(alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho)
        return (alpha0,fAlpha0)

    def dfp(self,xk,xkPlusOne,gk,gkPlusOne,hk):
        """ Updates the inverse of the Hessian using the DFP update.

        :param xk: the first grid point
        :param xkplusone: the second grid point
        :param gk: the first gradient value
        :param gkplusone: the second gradient value
        :param hk: the inverse Hessian that will be updated
        :return: the updated inverse Hessian
        """
        deltaK = xkPlusOne - xk
        gammaK = gkPlusOne - gk
        secondTermNominator = dot(deltaK,transpose(deltaK))
        secondTermDenominator = dot(transpose(deltaK),gammaK)
        thirdTermNominator = dot(dot(hk,dot(gammaK,transpose(gammaK))),hk)
        thirdTermDenominator = dot(transpose(gammaK),dot(hk,gammaK))
        hkPlusOne = hk + secondTermNominator/secondTermDenominator - thirdTermNominator/thirdTermDenominator
        return hkPlusOne

    def bfgs(self,xk,xkPlusOne,gk,gkPlusOne,hk):
        """ Updates the inverse of the Hessian using the BFGS update.

        :param xk: the first grid point
        :param xkPlusOne: the second grid point
        :param gk: the first gradient value
        :param gkPlusOne: the second gradient value
        :param hk: the inverse Hessian that will be updated
        :return: the updated inverse Hessian
        """

        deltaK = xkPlusOne - xk
        gammaK = gkPlusOne - gk
        secondTerm = (1+dot(dot(transpose(gammaK),hk),gammaK)/dot(transpose(deltaK),gammaK)) \
        * dot(deltaK,transpose(deltaK))/dot(transpose(deltaK),gammaK)
        thirdTerm = (dot(deltaK,dot(transpose(gammaK),hk)) + dot(hk,dot(gammaK,transpose(deltaK)))) \
        / dot(transpose(deltaK),gammaK)
        hkPlusOne = hk + secondTerm - thirdTerm
        return hkPlusOne

    def goodBroyden(self,x1,x0,g1,g0,H0):
        '''
        Updates the inverse of the Hessian H0 to H1 by the "Good Broyden" method. The input
        variables x1 and x0 are the current and previous vectors where the 
        objective function is evaluated. The variables g1 and g0 are the corresponding
        gradients. H0 is the previous inverse Hessian.
        The input variables have to be row vectors.
        :return: the updated inverse Hessian
        '''
        #Optionally the gradient is calculated inside i.e. g1=gradient(f(x1))
        delta=x1-x0
        gamma=g1-g0
        u=delta-dot(H0,gamma)
        a=1/(dot(transpose(u),gamma))
        H1=H0+a*dot(u,transpose(u))  
        return H1


    def badBroyden(self,x1,x0,g1,g0,H0):
        '''
        Updates the inverse of the Hessian H0 to H1 by the "Bad Broyden" method. The input
        variables x1 and x0 are the current and previous vectors where the 
        objective function is evaluated. The variables g1 and g0 are the corresponding
        gradients. H0 is the previous inverse Hessian.
        The input variables have to be row vectors.
        :return: the updated inverse Hessian
        '''
        #Optionally the gradient is calculated inside i.e. g1=gradient(f(x1))    
        delta=x1-x0
        gamma=g1-g0
        v=(delta-dot(H0,gamma))/(dot(transpose(gamma),gamma))
        H1=H0+dot(v,transpose(gamma))
        return H1

    def lineSearch(self,x,s,alpha0=1,rho=0.1,sigma=0.7,tau=0.1,chi=9):
        """
        Global linesearch method, inherit this method in QuasiNewton.py. This method acts as a placeholder,
        This function is just returning alpha=1 (no linesearch)
        """
        return 1

    def updateHessian(self):
        """
        Global method for finding the hessian or the inverse of the hessian
        inherit this method in QuasiNewton.py. This method acts as a placeholder,
        DONT IMPLEMENT ANYTHING HERE!
        """
    def finiteDifference(self,xk):
        """
        Does a simple central finite difference approximation of the hessian at point xk
        :return: h, symmetrized finite difference approximation of Hessian
        """
        h = np.array([numpy.array([0*len(xk)])*len(xk)]) # preallocate matrix of size len(xk)*len(xk)
        for i in range(len(xk)):
            for j in range(len(xk)):
                h[i,j] = (self.optProb.g(xk[i]+0.5e-5)[j]-self.optProb.g(xk[i]-0.5e-5)[j])/1e-5
        h = 1/2*(h+h.T)
        return h

    def lc(self,alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho=0.1,sigma=0.7):
        """
        defines the condition for the inexact linesearch (Placeholder)
        :return: boolean if the condition is fulfilled
        DONT IMPLEMENT ANYTHING HERE!
        """

    def rc(self,alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho=0.1):
        """
        defines the condition for the inexact linesearch (Placeholder)
        :return: boolean if the condition is fulfilled
        DONT IMPLEMENT ANYTHING HERE!
        """

    def lcWolfePowell(self,alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho=0.1,sigma=0.7):
        """
        defines the condition for the inexact linesearch (used: Wolfe-Powell)
        :return: boolean if the condition is fulfilled
        """
        if rho<0 or rho>0.5:
            raise Exception('rho needs to be an element of [0,0.5], but rho is:',rho)
        if sigma<0 or sigma>1:
            raise Exception('sigma needs to be an element of [0,1], but sigma is:',sigma)
        if sigma<=rho:
            raise Exception('(rho>=sigma) The value for rho needs to be less then the value of sigma! rho,sigma=',rho,sigma)
        if gAlpha0>=sigma*gAlphaL:
            return True
        return False

    def rcWolfePowell(self,alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho=0.1):
        """
        defines the condition for the inexact linesearch (used: Wolfe-Powell)
        :return: boolean if the condition is fulfilled
        """
        if rho<0 or rho>0.5:
            raise Exception('rho needs to be an element of [0,0.5], but rho is:',rho)
        if fAlpha0<=fAlphaL+rho*(alpha0-alphaL)*gAlphaL:
            return True
        return False

    def lcGoldstein(self,alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho=0.1,sigma=0.7):
        """
        defines the condition for the inexact linesearch (used: Wolfe-Powell)
        :return: boolean if the condition is fulfilled
        """
        if rho<0 or rho>0.5:
            raise Exception('rho needs to be an element of [0,0.5], but rho is:',rho)
        if fAlpha0>=(1-rho)*(alpha0-alphaL)*gAlphaL:
            return True
        return False

    def rcGoldstein(self,alpha0,alphaL,fAlpha0,gAlpha0,fAlphaL,gAlphaL,rho=0.1):
        """
        defines the condition for the inexact linesearch (used: Wolfe-Powell)
        :return: boolean if the condition is fulfilled
        """
        if rho<0 or rho>0.5:
            raise Exception('rho needs to be an element of [0,0.5], but rho is:',rho)
        if fAlpha0<=fAlphaL+rho*(alpha0-alphaL)*gAlphaL:
            return True
        return False
        
    def getSearchDir(self,g,H):
        """
        Global method for finding the search direction. This method acts as a placeholder,
        DONT IMPLEMENT ANYTHING HERE!
        H is the Hessian or the inverse of the Hessian (depends on the algortihm)
        """
        

    def getSearchDirHessian(self,g,H):
        """
        Find the corresponding search direction.
        H is the Hessian
        """
        return np.linalg.solve(H,-g)
        
    def getSearchDirInv(self,g,H):
        """ Global method for finding the search direction. This method acts as a placeholder,
        DONT IMPLEMENT ANYTHING HERE!
        H is the Hessian or the inverse of the Hessian (depends on the algortihm)
        """
        return -H.dot(g)
        
    def isPosDef(self,H):
        """
        Checks if the matrix is positive definite
        :return: True (if the matrix is positive definite)
                 False (else)
        """
        try: 
            np.cholesky(H)
            return True
        except:
            return False

   def finiteDifference(self,xk):
        """
        Does a simple central finite difference approximation of the hessian at point xk
        :return: h, symmetrized finite difference approximation of Hessian
        """
        # preallocate matrix of size len(xk)*len(xk)
        # h = np.zeros((len(xk), len(xk)))
        h = np.array([[(self.optProb.g(xk+0.5e-5*np.eye(1,len(xk),i)[0])[j]- \
        self.optProb.g(xk-0.5e-5*np.eye(1,len(xk),i)[0])[j])/1e-5 for j in range(len(xk))] \
        for i in range(len(xk))])
        h = 1/2*(h+h.T)
        return h
