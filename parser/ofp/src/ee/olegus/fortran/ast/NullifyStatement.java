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
public class NullifyStatement extends Statement {
	
	private List<DataReference> arguments;

	public List<DataReference> getArguments() {
		return arguments;
	}

	public void setArguments(List<DataReference> arguments) {
		this.arguments = arguments;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
	
}
