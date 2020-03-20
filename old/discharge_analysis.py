#!/usr/bin/env python

# measure discharge from 7.891 to 6.000

def main():
    data = {}
    for num in range(1, 49):
        path = "discharge_logs/%d.log" % num
        t_total = 0.0
        c_total = 0.0
        t_prev = 0.0
        v_prev = 0.0
        with open(path) as fin:
            for line in fin:
                line = line.strip()
                t = float(line.split('\t')[0])
                v = float(line.split('\t')[1])
                if v >= 7.891:
                    t_total = 0.0
                    c_total = 0.0
                elif v < 6.0:
                    break
                else:
                    t_diff = t - t_prev
                    c = t_diff * v
                    t_total += t_diff
                    c_total += c
                t_prev = t
                v_prev = v
        print "%.0f\t%.0f" % (t_total, c_total)

if __name__== "__main__":
    main()
