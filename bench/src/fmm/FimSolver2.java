/****************************************************************************
Copyright (c) 2008, Colorado School of Mines and others. All rights reserved.
This program and accompanying materials are made available under the terms of
the Common Public License - v1.0, which accompanies this distribution, and is 
available at http://www.eclipse.org/legal/cpl-v10.html
****************************************************************************/
package fmm;

import edu.mines.jtk.util.*;
import static edu.mines.jtk.util.MathPlus.*;

// for testing
import java.awt.*;
import java.awt.image.*;
import java.io.*;
import java.util.*;
import javax.swing.JFrame;
import javax.swing.SwingUtilities;
import edu.mines.jtk.awt.*;
import edu.mines.jtk.dsp.*;
import edu.mines.jtk.io.*;
import edu.mines.jtk.mosaic.*;

/**
 * 2D implementation of Jeong and Whitakers' fast iterative method.
 * @author Dave Hale, Colorado School of Mines
 * @version 2008.07.12
 */
public class FimSolver2 {

  /**
   * An interface for classes of diffusion tensors. Each tensor is a
   * symmetric positive-definite 2-by-2 matrix {{d11,d12},{d12,d22}}.
   */
  public interface Tensors {

    /**
     * Gets diffusion tensor elements for specified indices.
     * @param i1 index for 1st dimension.
     * @param i2 index for 2nd dimension.
     * @param d array {d11,d12,d22} of tensor elements.
     */
    public void getTensor(int i1, int i2, float[] d);
  }

  /**
   * Constructs a solver with constant identity diffusion tensors.
   * @param n1 number of samples in 1st dimension.
   * @param n2 number of samples in 2nd dimension.
   */
  public FimSolver2(int n1, int n2) {
    this(n1,n2,new IdentityTensors());
  }
  
  /**
   * Constructs a solver for the specified diffusion tensor field.
   * @param t array of times to be computed by this solver; by reference.
   * @param n1 number of samples in 1st dimension.
   * @param n2 number of samples in 2nd dimension.
   * @param dt diffusion tensors.
   */
  public FimSolver2(int n1, int n2, Tensors dt) {
    _n1 = n1;
    _n2 = n2;
    _dt = dt;
    _t = new float[n2][n1];
  }

  /**
   * Returns times computed for sources at specified locations.
   * @param s array of flags: true, for source samples; false, otherwise.
   * @return array of times.
   */
  public float[][] solve(boolean[][] s) {
    initialize(s);
    solve();
    return _t;
  }

  ///////////////////////////////////////////////////////////////////////////
  // private

  // Diffusion tensors.
  private static class IdentityTensors implements Tensors {
    public void getTensor(int i1, int i2, float[] d) {
      d[0] = 1.00f; // d11
      d[1] = 0.00f; // d12
      d[2] = 1.00f; // d22
    }
  }

  private static final float INFINITY = Float.MAX_VALUE;

  private static final int[] K1 = {-1, 1, 0, 0};
  private static final int[] K2 = { 0, 0,-1, 1};

  private static class Index {
    int i1,i2;
    Index(int i1, int i2) {
      this.i1 = i1;
      this.i2 = i2;
    }
    public boolean equals(Object o) {
      Index i = (Index)o;
      return i.i1==i1 && i.i2==i2;
    }
    public int hashCode() {
      return i1^i2;
    }
  }

  private int _n1,_n2;
  private Tensors _dt;
  private float[][] _t;
  private HashMap<Index,Index> _as = new HashMap<Index,Index>(1024);

  private void activate(int i1, int i2) {
    if (0<=i1 && i1<_n1 &&
        0<=i2 && i2<_n2) {
      Index i = new Index(i1,i2);
      _as.put(i,i);
    }
  }

  private void deactivate(Index i) {
    _as.remove(i);
  }

  private void initialize(boolean[][] s) {
    for (int i2=0; i2<_n2; ++i2) {
      for (int i1=0; i1<_n1; ++i1) {
        if (s[i2][i1]) {
          _t[i2][i1] = 0.0f;
          for (int k=0; k<4; ++k)
            activate(i1+K1[k],i2+K2[k]);
        } else {
          _t[i2][i1] = INFINITY;
        }
      }
    }
  }

  private void solve() {
    Index jj = new Index(-1,-1);
    Index[] ia = new Index[_n1*_n2];
    float epsilon = 0.01f;
    for (int niter=0; !_as.isEmpty() && niter<1000; ++niter) {
      int n = _as.size();
      trace("niter="+niter+" n="+n);
      _as.keySet().toArray(ia);
      for (int i=0; i<n; ++i) {
        Index ii = ia[i];
        int i1 = ii.i1;
        int i2 = ii.i2;
        float ti = _t[i2][i1];
        float gi = g(i1,i2);
        _t[i2][i1] = gi;
        if (ti-gi<ti*epsilon) {
          for (int k=0; k<4; ++k) {
            int j1 = i1+K1[k];
            int j2 = i2+K2[k];
            if (j1<0 || j1>=_n1 || j2<0 || j2>=_n2) 
              continue;
            jj.i1 = j1;
            jj.i2 = j2;
            if (!_as.containsKey(jj)) {
              float gj = g(j1,j2);
              if (gj<_t[j2][j1]) {
                _t[j2][j1] = gj;
                activate(j1,j2);
              }
            }
          }
          deactivate(ii);
        }
      }
    }
  }

  /**
   * Solves the quadratic equation
   *   d11*s1*s1*(t1-t)*(t1-t) + 
   * 2*d12*s1*s2*(t1-t)*(t2-t) + 
   *   d22*s2*s2*(t2-t)*(t2-t) = 1
   * for a positive time t. If no solution exists, because the 
   * discriminant is negative, this method returns INFINITY.
   */
  private static float solveQuadratic(
    float d11, float d12, float d22,
    float s1, float s2, float t1, float t2) 
  {
    double ds11 = d11*s1*s1;
    double ds12 = d12*s1*s2;
    double ds22 = d22*s2*s2;
    double t12 = t1-t2; // reduce rounding errors by solving for u = t-t1
    double a = ds11+2.0*ds12+ds22;
    double b = 2.0*(ds12+ds22)*t12;
    double c = ds22*t12*t12-1.0;
    double d = b*b-4.0*a*c;
    if (d<0.0) 
      return INFINITY;
    double u = (-b+sqrt(d))/(2.0*a);
    return t1+(float)u;
  }

  /**
   * Tests time differences for a valid solution. 
   * Parameters tm and tp are times for samples backward and forward of 
   * the sample with time t0. The parameter k is the index k1 or k2 that 
   * was used to compute the time, and the parameter p is the derivative 
   * p1 or p2 that is a critical point of H(p1,p2), where either p1 or p2
   * is fixed.
   */
  private static boolean isValid(
    float tm, float tp, float t0, int k, float p) 
  {
    float pm = t0-tm;
    float pp = tp-t0;
    int j = -1;
    if (pm<p && p<pp) { // (pm-p) < 0 and (pp-p) > 0
      j = 0;
    } else if (0.5f*(pm+pp)<p) { // (pm-p) < -(pp-p)
      j = 1;
    }
    return j==k;
  }

  /**
   * Returns true if valid time differences in 1st dimension.
   */
  private boolean isValid1(int i1, int i2, int k1, float p1, float t0) {
    float tm = (i1>0    )?_t[i2][i1-1]:INFINITY;
    float tp = (i1<_n1-1)?_t[i2][i1+1]:INFINITY;
    return isValid(tm,tp,t0,k1,p1);
  }

  /**
   * Returns true if valid time differences in 2nd dimension.
   */
  private boolean isValid2(int i1, int i2, int k2, float p2, float t0) {
    float tm = (i2>0    )?_t[i2-1][i1]:INFINITY;
    float tp = (i2<_n2-1)?_t[i2+1][i1]:INFINITY;
    return isValid(tm,tp,t0,k2,p2);
  }

  /**
   * Returns a valid time t computed via the Godunov-Hamiltonian.
   */
  private float g(int i1, int i2) {
    float tmin = _t[i2][i1];

    // Get tensor coefficients.
    float[] d = new float[3];
    _dt.getTensor(i1,i2,d);
    float d11 = d[0];
    float d12 = d[1];
    float d22 = d[2];

    // For (p1-,p2-), (p1+,p2-), (p1-,p2+), (p1+,p2+)
    for (int k2=-1; k2<=1; k2+=2) {
      int j2 = i2+k2;
      if (j2<0 || j2>=_n2) continue;
      float t2 = _t[j2][i1];
      for (int k1=-1; k1<=1; k1+=2) {
        int j1 = i1+k1;
        if (j1<0 || j1>=_n1) continue;
        float t1 = _t[i2][j1];
        if (t1!=INFINITY && t2!=INFINITY) {
          float s1 = k1;
          float s2 = k2;
          float t0 = solveQuadratic(d11,d12,d22,s1,s2,t1,t2);
          if (t0<tmin && t0>=min(t1,t2)) {
            float p1 = -s2*(t2-t0)*d12/d11;
            float p2 = -s1*(t1-t0)*d12/d22;
            if (isValid1(i1,i2,k1,p1,t0) &&
                isValid2(i1,i2,k2,p2,t0)) {
              tmin = t0;
            }
          }
        }
      }
    }

    // For (p1s,p2-), (p1s,p2+)
    for (int k2=-1; k2<=1; k2+=2) {
      int j2 = i2+k2;
      if (j2<0 || j2>=_n2) continue;
      float t2 = _t[j2][i1];
      if (t2!=INFINITY) {
        float t1 = t2;
        float s2 = k2;
        float s1 = -s2*d12/d11;
        float t0 = solveQuadratic(d11,d12,d22,s1,s2,t1,t2);
        if (t0<tmin && t0>=t2) {
          float p2 = -s1*(t1-t0)*d12/d22;
          if (isValid2(i1,i2,k2,p2,t0)) {
            tmin = t0;
          }
        }
      }
    }
  
    // For (p1-,p2s), (p1+,p2s)
    for (int k1=-1; k1<=1; k1+=2) {
      int j1 = i1+k1;
      if (j1<0 || j1>=_n1) continue;
      float t1 = _t[i2][j1];
      if (t1!=INFINITY) {
        float t2 = t1;
        float s1 = k1;
        float s2 = -s1*d12/d22;
        float t0 = solveQuadratic(d11,d12,d22,s1,s2,t1,t2);
        if (t0<tmin && t0>=t1) {
          float p1 = -s2*(t2-t0)*d12/d11;
          if (isValid1(i1,i2,k1,p1,t0)) {
            tmin = t0;
          }
        }
      }
    }

    return tmin;
  }

  ///////////////////////////////////////////////////////////////////////////
  ///////////////////////////////////////////////////////////////////////////
  ///////////////////////////////////////////////////////////////////////////
  // testing

  private static class ConstantTensors implements FimSolver2.Tensors {
    ConstantTensors(float d11, float d12, float d22) {
      _d11 = d11;
      _d12 = d12;
      _d22 = d22;
    }
    public void getTensor(int i1, int i2, float[] d) {
      d[0] = _d11;
      d[1] = _d12;
      d[2] = _d22;
    }
    private float _d11,_d12,_d22;
  }

  private static void plot(float[][] x) {
    float[][] y = Array.copy(x);
    int n1 = y[0].length;
    int n2 = y.length;
    for (int i2=0; i2<n2; ++i2) {
      for (int i1=0; i1<n1; ++i1) {
        if (y[i2][i1]==INFINITY)
          y[i2][i1] = 0.0f;
      }
    }
    SimplePlot sp = new SimplePlot();
    sp.setSize(800,790);
    PixelsView pv = sp.addPixels(y);
    pv.setColorModel(ColorMap.JET);
    pv.setInterpolation(PixelsView.Interpolation.NEAREST);
  }

  private static void testConstant() {
    int n1 = 101;
    int n2 = 101;
    float angle = FLT_PI*110.0f/180.0f;
    float su = 1.000f;
    float sv = 0.001f;
    float cosa = cos(angle);
    float sina = sin(angle);
    float d11 = su*cosa*cosa+sv*sina*sina;
    float d12 = (su-sv)*sina*cosa;
    float d22 = sv*cosa*cosa+su*sina*sina;
    trace("d11="+d11+" d12="+d12+" d22="+d22+" d="+(d11*d22-d12*d12));
    ConstantTensors dt = new ConstantTensors(d11,d12,d22);
    FimSolver2 fs = new FimSolver2(n1,n2,dt);
    boolean[][] s = new boolean[n2][n1];
    s[1*n2/4][1*n1/4] = true;
    //s[2*n2/4][2*n1/4] = true;
    s[3*n2/4][3*n1/4] = true;
    float[][] t = fs.solve(s);
    //Array.dump(t);
    plot(t);
  }

  private static void trace(String s) {
    System.out.println(s);
  }

  public static void main(String[] args) {
    SwingUtilities.invokeLater(new Runnable() {
      public void run() {
        testConstant();
      }
    });
  }
}
