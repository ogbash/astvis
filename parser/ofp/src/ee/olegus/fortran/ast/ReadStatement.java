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
public class ReadStatement extends Statement {
	private List<ActualArgument> controls;
	private List<Expression> inputs;
	
	public List<ActualArgument> getControls() {
		return controls;
	}
	public void setControls(List<ActualArgument> controls) {
		this.controls = controls;
	}
	public List<Expression> getInputs() {
		return inputs;
	}
	public void setInputs(List<Expression> outputs) {
		this.inputs = outputs;
	}
	public Object astWalk(ASTVisitor visitor) {
		if(inputs!=null) {
			for(Expression expr: inputs) {
				expr.astWalk(visitor);
			}
		}
		
		return visitor.visit(this);
	}
}
