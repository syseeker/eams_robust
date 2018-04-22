import numpy as np
from random import uniform

class Robust_Proc:

# dm    max delta    p(m)
# 1    1            0.39346934
# 2    1.414213562  0.632120559
# 3    1.732050808  0.77686984
# 4    2            0.864664717
# 5    2.236067977  0.917915001
# 6    2.449489743  0.950212932
# 7    2.645751311  0.969802617
# 8    2.828427125  0.981684361
# 9    3            0.988891003
# 10    3.16227766  0.993262053
# 11    3.31662479  0.995913229

    def __init__(self):
        
#         self.procedure(3.16227766, [10,9,8])
#         self.procedure(1.414213562, [10,9,8])
         
#         self.procedure(3.16227766, [10,9,8,7,6,5,4,3,2,1])
#         self.procedure(2.236067977, [10,9,8,7,6,5,4,3,2,1])
#         self.procedure(1.414213562, [10,9,8,7,6,5,4,3,2,1])


#         self.procedure(3.16227766, [-1] )        
#         self.procedure(1.414213562, [-1] )
#         self.procedure(3.16227766, [-1,-1] )
#         self.procedure(1.414213562, [-1,-1] )
#         self.procedure(3.16227766, [-1,-1,-1] )        
#         self.procedure(1.414213562, [-1,-1,-1] )
#         self.procedure(3.16227766, [-1,-1,-1,-1] )
#         self.procedure(1.414213562, [-1,-1,-1,-1] )

#         self.procedure(2, [-0.1] )
#         self.procedure(1.414213562, [-0.1] )
#         self.procedure(2, [-0.1,-0.1] )
#         self.procedure(1.414213562, [-0.1,-0.1] )
#         self.procedure(2, [-0.1,-0.1,-0.1] )
#         self.procedure(1.414213562, [-0.1,-0.1,-0.1] )
#         self.procedure(2, [-0.1,-0.1,-0.1,-0.1] )
#         self.procedure(1.414213562, [-0.1,-0.1,-0.1,-0.1] )
#                 
#         self.procedure(2, [0.1] )
#         self.procedure(1.414213562, [0.1] )
#         self.procedure(2, [0.1,0.1] )
#         self.procedure(1.414213562, [0.1,0.1] )
#         self.procedure(2, [0.1,0.1,0.1] )
#         self.procedure(1.414213562, [0.1,0.1,0.1] )
#         self.procedure(2, [0.1,0.1,0.1,0.1] )
#         self.procedure(1.414213562, [0.1,0.1,0.1,0.1] )


#         self.procedure(2, [0.1] )
#         self.procedure(1.414213562, [0.1] )
#          
#         self.procedure(1, [0.1,0.1] )
#         self.procedure(1.414213562, [0.1,0.1] )
#          
#         self.procedure(1, [0.1,0.1,0.1] )
#         self.procedure(1.414213562, [0.1,0.1,0.1] )
#          
#         self.procedure(1, [0.1,0.1,0.1,0.1] )
#         self.procedure(1.414213562, [0.1,0.1,0.1,0.1] )        
        
#         self.procedure(1, [-0.1] )
#         self.procedure(1.414213562, [-0.1] )
#         self.procedure(1, [-0.1,-0.1] )
#         self.procedure(1.414213562, [-0.1,-0.1] )
#         self.procedure(1, [-0.1,-0.1,-0.1] )
#         self.procedure(1.414213562, [-0.1,-0.1,-0.1] )
#         self.procedure(1, [-0.1,-0.1,-0.1,-0.1] )
#         self.procedure(1.414213562, [-0.1,-0.1,-0.1,-0.1] )        

        
#
#         self.procedure(3.16227766, [1,1,1,1,1,1,1,1,1] )
#         self.procedure(3.16227766, [-1,-1,-1,-1,-1,-1,-1,-1,-1] )
#         self.procedure(1.414213562, [1,1,1,1,1,1,1,1,1] )
#         self.procedure(1.414213562, [-1,-1,-1,-1,-1,-1,-1,-1,-1] )
#                 
#         self.procedure(3.16227766, [2.3,2.3,2.3])
#         self.procedure(1.414213562, [2.3,2.3,2.3])
#          
#         self.procedure(3.16227766, [2.3,2.3,2.3,2.3,2.3,2.3,2.3,2.3,2.3])
#         self.procedure(1.414213562, [2.3,2.3,2.3,2.3,2.3,2.3,2.3,2.3,2.3])
#         
#         self.procedure(3.16227766, [0.7,0.25,0.1])
#         self.procedure(1.414213562, [0.7,0.25,0.1])
#             

#         self.procedure(3.16227766, [0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7] )
#         self.procedure(2, [0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7] )
#         self.procedure(1.414213562, [0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7,0.7] )
        
#         self.procedure(3.16227766, [0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166], [0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166], )
#         self.procedure(2, [0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166],[0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166], )
#         self.procedure(1.414213562, [0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166],[0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166,0.01166], )        
    
#         self.procedure(3.16227766, 0.99, 0.7*10, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35], [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#         self.procedure(2, 0.86, 0.7*10, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#         self.procedure(1.414213562, 0.63, 0.7*10, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#                 
#         self.procedure(3.16227766, 0.98, 0.7*10, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35], [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#         self.procedure(2, 0.80, 0.7*10, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#         self.procedure(1.414213562, 0.55, 0.7*10, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
       
#         self.procedure(3.16227766, 0.99, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35], [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#         self.procedure(2, 0.86, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
#         self.procedure(1.414213562, 0.63, [0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35],[0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35,0.35])
      
#         self.procedure(1, 0.39, [0.35,0.35],[0.35,0.35])


#         self.procedure(1, [0],[1])
#         self.procedure(1.414213562, [0],[1])
#         self.procedure(3.16227766, [0],[1])
        
#         self.procedure(1, [0,0],[1,1])
#         self.procedure(1.414213562, [0,0],[1,1])
#         self.procedure(3.16227766, [0,0],[1,1])
        
#         self.procedure(3.16227766, [0],[0.5])     # 99%        
        self.procedure(1.414213562, '74%', [0],[0.5])    # 74%
        self.procedure(1, '50%', [0],[0.5])              # 50%
        
#         self.procedure(3.16227766, [0,0],[0.5,0.5])     # 99%
        self.procedure(1.414213562, '74%', [0,0],[0.5,0.5])    # 74%
        self.procedure(1, '50%', [0,0],[0.5,0.5])              # 50%
                
#         self.procedure(3.16227766, [0,0,0],[0.5,0.5,0.5])     # 99%
        self.procedure(1.414213562, '74%', [0,0,0],[0.5,0.5,0.5])    # 74%
        self.procedure(1, '50%', [0,0,0],[0.5,0.5,0.5])              # 50%
                
#         self.procedure(3.16227766, [0,0,0,0],[0.5,0.5,0.5,0.5])     # 99%
#         self.procedure(1.414213562, '74%', [0,0,0,0],[0.5,0.5,0.5,0.5])    # 74%
#         self.procedure(1, '50%', [0,0,0,0],[0.5,0.5,0.5,0.5])              # 50%
        
   
    
    def procedure(self, delta, prob_guar , a_bar, a):
        S = []
        n = len(a)        
        k = 1
        
        if delta > np.sqrt(len(a)):
            print a, " ", delta, " Error: delta > np.sqrt(len(a)) --- ", delta, " > ",  np.sqrt(len(a))# ,"\n"
            return
            
        while k < n-1:
            numer = np.sqrt(delta**2 - len(S)) * abs(a[k-1])
            denom = np.sqrt(np.sum([(x**2) for x in a[k-1:]]))
                                      
#             print k, " ", delta**2, " ", len(S), " ", delta**2 - len(S), " ", np.sqrt(delta**2 - len(S)),  "*", abs(a[k]), "   ", numer, " ", denom
#             print k, " ", numer, " ", denom
            if numer/denom <= 1:                
                break
            else:
                S.append(k)
                k = k+1
              
#         print S
          
        a_hat_sum = 0
        for i in S:
            a_hat_sum += a[i-1]
            
        slack = np.sum(a_bar) + a_hat_sum + np.sqrt(
                                     (delta**2-len(S))*
                                     np.sum([(x**2) for x in a[len(S):]])
                                     )
        
                                                    
#         print a, " ", delta, " ", prob_guar, " ", slack, " ", 1.75-slack
        print a, " ", delta, " ", prob_guar, " ", slack, " ", 3.33-slack
        
        
                     
#         
#         
#     def gen_rand(self, total_run, slack, delta):
#         count = 0
#         for i in xrange(total_run):
#             x = []
#             for j in xrange(2):
#                 x.append(uniform(0, 0.7))
# #                 x.append(uniform(-1, 1)*0.35)
# #                 x.append(uniform(-0.35, 0.35))
#                 
#             print x, " ", np.sum(x)
#             if np.sum(x) > 5.6 and slack <= 5.6: #slack:
#                 print count
#                 count += 1
#                 
#         print float(count)/total_run*100, " ", np.exp(-(delta**2)/2), " ", np.exp(-(delta**2)/1.5)
#         
#             
    
            
            
#        
#     def procedure(self, delta, prob_guar, a_bar, a):
#         S = []
#         n = len(a)        
#         k = 1
#         
# #         if delta > np.sqrt(len(a)):
# #             print "Error: delta > np.sqrt(len(a))"
# #             return
#             
#         while k < n-1:
#             numer = np.sqrt(delta**2 - len(S)) * abs(a[k-1])
#             denom = np.sqrt(np.sum([(x**2) for x in a[k-1:]]))
#                                       
# #             print k, " ", delta**2, " ", len(S), " ", delta**2 - len(S), " ", np.sqrt(delta**2 - len(S)),  "*", abs(a[k]), "   ", numer, " ", denom
# #             print k, " ", numer, " ", denom
#             if numer/denom <= 1:                
#                 break
#             else:
#                 S.append(k)
#                 k = k+1
#               
#         print S
#           
#         a_hat_sum = 0
#         for i in S:
#             a_hat_sum += a[i-1]
#             
#         #slack = np.sum(a_bar) + a_hat_sum + np.sqrt(
# #                                     (delta**2-len(S))*
# #                                     np.sum([(x**2) for x in a[len(S):]])
# #                                     )
#                                     
#         slack = a_hat_sum + np.sqrt(
#                                     (delta**2-len(S))*
#                                     np.sum([(x**2) for x in a[len(S):]])
#                                     )
#         
#         area = delta*np.sqrt(len(a))*0.35
#         print a, " ", delta, " ", prob_guar, " ", slack, " ", area#, " diff:", round((slack-(prob_guar*area))/(prob_guar*area)*100,2), "%" #, " ", float(slack)/30
#         print " "
#         self.gen_rand(10, slack, delta)
                 
    
r = Robust_Proc()