import ast
class FaceDetection:
    def __init__(self,detection):
        self.bounding_box = [(detection[0],detection[1]),(detection[2],detection[3])]
        if len(detection)>4:
            self.right_eye = (detection[5], detection[6])
            self.left_eye = (detection[7],detection[8])
            self.nose = (detection[9],detection[10])
            self.right_lip = (detection[11],detection[12])
            self.left_lip = (detection[13],detection[14])

    def get_facial5points(self):
        return [self.right_eye,self.left_eye,self.nose,self.right_lip,self.left_lip]
    def size(self):
        [(x0,y0),(x1,y1)] = self.bounding_box
        return abs(x1-x0) * abs(y1-y0)
    @property
    def width(self):
        return abs(self.bounding_box[1][0]-self.bounding_box[0][0])
    @property
    def height(self):
        return abs(self.bounding_box[1][1]-self.bounding_box[0][1])
    @property
    def area(self):
        return self.width * self.height
    def contains_point(self,point):
        (x,y) = point
        x_min = min(self.bounding_box[0][0],self.bounding_box[1][0])
        y_min = min(self.bounding_box[0][1],self.bounding_box[1][1])
        x_max = max(self.bounding_box[0][0],self.bounding_box[1][0])
        y_max = max(self.bounding_box[0][1],self.bounding_box[1][1])
        if x<x_min or x>x_max or y<y_min or y>y_max:
            return False
        return True

    def to_json(self):
        return str(self.__dict__)

    @staticmethod
    def from_json(json):
        new_detection = FaceDetection([0, 0, 0, 0])
        new_detection.__dict__ = ast.literal_eval(json)
        return new_detection