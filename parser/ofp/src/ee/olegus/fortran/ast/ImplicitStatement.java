/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ASTVisitor;

/**
 * "Implicit None" or "Implicit <list>"
 * 
 * @author olegus
 *
 */
public class ImplicitStatement extends Declaration {

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

}
