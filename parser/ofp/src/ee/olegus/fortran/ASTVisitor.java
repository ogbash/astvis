/**
 * 
 */
package ee.olegus.fortran;

import ee.olegus.fortran.ast.Code;
import ee.olegus.fortran.ast.Expression;
import ee.olegus.fortran.ast.Statement;

/**
 * @author olegus
 *
 */
public interface ASTVisitor {
	/**
	 * @param expr to visit
	 * @return expr to replace with
	 */
	Expression visit(Expression expr);
	Statement visit(Statement stmt);
	
	void enter(Code code);
	void leave(Code code);
}
