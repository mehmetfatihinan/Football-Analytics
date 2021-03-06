__author__ = 'aliuzun'
import csv
import os
import math
import numpy
from sklearn import svm
import matplotlib.pyplot as plt
from src.sentio.Parameters import DATA_BASE_DIR
from src.sentio.file_io.reader.XMLreader import XMLreader



class HeatMapForPass():
    def __init__(self):
        pass

    def WriteToCSV(self):
        reader = XMLreader(os.path.join(DATA_BASE_DIR, 'output/sentio_data.xml'))
        game_instances, slider_mapping = reader.parse()

        container = list()
        container.extend(["Pass Starting Point(X)","Pass Starting Point(Y)","Pass Ending Point(X)","Pass Ending Point(Y)","Status"])
        out = csv.writer(open("files/awayTeamFirstHalfPass.csv","w"), delimiter='\t', quoting=csv.QUOTE_NONE)
        out.writerow(container)
        del container[:]


        for game_instance in game_instances.getFirstHalfInstances():
            if game_instance.event and game_instance.event.isPassEvent():
                pass_event = game_instance.event.pass_event
                x1s,y1s = pass_event.pass_source.get_position()
                x2s,y2s = pass_event.pass_target.get_position()
                status = pass_event.isSuccessful()

                if not pass_event.pass_source.isHomeTeamPlayer():
                    if status == True: container.extend([x1s,y1s,x2s,y2s, "T"])
                    else: container.extend([x1s,y1s,x2s,y2s, "F"])
                    out.writerow(container)
                    del container[:]

    def readFile(self,filename):
        coordinates,statusus=[],[]
        path="csv_files/" + filename
        with open(path) as file:
            file.readline()
            data = csv.reader(file, delimiter="\t")
            for line in data:
                coordinates.append(line[0:4])
                statusus.append(line[-1])
        return coordinates,statusus

    def getCount(selfself,filename):
        Fcount,Tcount=0,0
        path="csv_files/" + filename
        with open(path) as file:
            file.readline()
            data = csv.reader(file, delimiter="\t")
            for line in data:
                if line[-1] == "F": Fcount+=1
                else: Tcount +=1
        return "T:",Tcount,"F",Fcount




    def getPasses(self,PassStartingPoint,radius,filename):


        F_point,T_point,F_status,T_status=[],[],[],[]
        points,statuses=self.readFile(filename)
        for index in range(len(statuses)):
            # print points[0:2][index]
            if statuses[index]=="T":
                T_point.append(points[index])
                T_status.append(statuses[index])
            else:
                T_point.append(points[index])
                T_status.append(statuses[index])
        points=T_point[0:35]+ F_point[0:35]
        statuses=T_status[0:35]+ F_status[0:35]
        print points
        s_x,s_y = PassStartingPoint

        clf=svm.SVC(C=3, cache_size=300, class_weight=None, coef0=0.0, degree=3,
            gamma=0.0005, kernel='rbf', max_iter=-1, probability=True, random_state=None,
            shrinking=True, tol=0.001, verbose=False)

        clf.fit(points,statuses)

        x_points, y_points = 210,140
        x_coord = numpy.linspace(0, 70, x_points)
        y_coord = numpy.linspace(0, 105, y_points)

        data=[]

        for y in y_coord:
            val=[]
            for x in x_coord:
                v=(numpy.array(clf.predict_proba([s_x,s_y,x,y])).tolist())
                val.append(v[0][1])
            data.append(val)
        # print min(data[0]),max(data[0])

        scat_xf,scat_yf,scat_xt,scat_yt=[],[],[],[]

        for index,point in enumerate(points):
            x1,y1,x2,y2 = float(point[0]),float(point[1]),float(point[2]),float(point[3])
            r = math.sqrt(math.pow((s_x-x1),2) + math.pow((s_y-y1),2))
            if r <= radius:
                if statuses[index] == "F":
                    scat_xf.append(x2)
                    scat_yf.append(y2)
                else:
                    scat_xt.append(x2)
                    scat_yt.append(y2)

        hm= plt.figure(figsize=(15,8))
        plt.scatter(s_x,s_y,s=80,c="green",label = "Source of Pass")

        plt.matplotlib.pyplot.scatter(scat_xf,scat_yf,s=30,c='blue',label = "Unsuccessful Pass")
        plt.matplotlib.pyplot.scatter(scat_xt,scat_yt,s=30,c='red',label = "Successful Pass")
        im2 = plt.imread('/Users/aliuzun/PycharmProjects/futbol-data-analysis/src/sentio/Sklearn/srcc/background.png',0)


        hm = plt.imshow(im2, extent=[-2.0, 107.0, 72.0, 0.0], aspect="auto")

        hm = plt.imshow(data, interpolation='bilinear', extent=[0.0, 105.0, 70.0, 0.0], alpha=0.8)


        plt.suptitle(filename[0:len(filename)-4])

        plt.colorbar()
        plt.legend(ncol=3,fontsize=9,bbox_to_anchor=(0.51,0.051))
        plt.show()



    def showAllPass(self,filename):

        points,statuses=self.readFile(filename)
        lx1,lx2,ly1,ly2=[],[],[],[]
        scat_xf,scat_yf,scat_xt,scat_yt=[],[],[],[]

        for index,point in enumerate(points):
            x1,y1,x2,y2=point
            lx1.append(x1),ly1.append(y1),lx2.append(x2),ly2.append(y2)

            if statuses[index] == "F":
                scat_xf.extend([x1,x2])
                scat_yf.extend([y1,y2])
            else:
                scat_xt.extend([x1,x2])
                scat_yt.extend([y1,y2])

        #lines
        # line_x,line_y = [lx1,lx2],[ly1,ly2]
        # plt.plot(line_x,line_y,c="r")
        hm= plt.figure(figsize=(10,7))

        plt.scatter(scat_xf,scat_yf,marker='o',c='blue',label = "Unsuccessful Pass")
        plt.scatter(scat_xt,scat_yt,marker='o',c='red',label = "Successful Pass")

        im2=plt.imread('/Users/aliuzun/PycharmProjects/futbol-data-analysis/src/sentio/Sklearn/srcc/background.png',0)

        hm=plt.imshow(im2, extent=[-2.0, 107.0, 72.0, 0.0], aspect="auto")
        plt.suptitle(filename[0:len(filename)-4])


        plt.legend(ncol=2,fontsize=9,bbox_to_anchor=(0.415,0.052))


        plt.show()



if __name__ == "__main__":
    tp=(52.0,35.1)
    w=HeatMapForPass()
    print w.getPasses(tp,15.0,"awayTeamAll.csv") #"homeTeamFirstHalfPass.csv"
    # print w.showAllPass("awayTeamAll.csv")
    # print w.WriteToCSV()
    # print w.getCount("homeTeamAll.csv")

