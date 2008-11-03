/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.List;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class WriteStatement extends Statement {
	private List<ActualArgument> controls;
	private List<Expression> outputs;
	
	public List<ActualArgument> getControls() {
		return controls;
	}
	public void setControls(List<ActualArgument> controls) {
		this.controls = controls;
	}
	public List<Expression> getOutputs() {
		return outputs;
	}
	public void setOutputs(List<Expression> outputs) {
		this.outputs = outputs;
	}
	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
