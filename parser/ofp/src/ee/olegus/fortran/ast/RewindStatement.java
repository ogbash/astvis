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
public class RewindStatement extends Statement {
	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
