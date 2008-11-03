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
public class PrintStatement extends Statement {
	private Expression format;
	private List<Expression> outputs;

	public List<Expression> getOutputs() {
		return outputs;
	}

	public void setOutputs(List<Expression> outputs) {
		this.outputs = outputs;
	}

	public Expression getFormat() {
		return format;
	}

	public void setFormat(Expression format) {
		this.format = format;
	}

	public Object astWalk(ASTVisitor visitor) {
		for(Expression output: outputs) {
			output.astWalk(visitor);
		}
		
		return visitor.visit(this);
	}

}
