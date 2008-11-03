/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class ReturnStatement extends Statement {

	private Expression expression;

	public Expression getExpression() {
		return expression;
	}

	public void setExpression(Expression expression) {
		this.expression = expression;
	}

	public Object astWalk(ASTVisitor visitor) {
		if(expression!=null) {
			expression.astWalk(visitor);
		}
		
		return visitor.visit(this);
	}
}
