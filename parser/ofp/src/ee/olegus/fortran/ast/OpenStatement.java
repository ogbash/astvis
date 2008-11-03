/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class OpenStatement extends Statement {

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

}
