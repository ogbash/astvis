/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class CloseStatement extends Statement {

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
