/**
 * 
 */
package ee.olegus.fortran.visitors;

import ee.olegus.fortran.ASTVisitor;
import ee.olegus.fortran.Model;
import ee.olegus.fortran.ast.DataReference;
import ee.olegus.fortran.ast.Expression;
import ee.olegus.fortran.ast.FunctionCall;
import ee.olegus.fortran.ast.Statement;

/**
 * @author olegus
 *
 */
public class DataReferenceResolver extends ASTVisitorContext implements
		ASTVisitor {

	public DataReferenceResolver(Model model) {
		super(model);
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitor#visit(ee.olegus.fortran.ast.Expression)
	 */
	public Expression visit(Expression expr) {
		if(expr instanceof DataReference) {
			DataReference ref = (DataReference) expr;
			if(ref.getBase()==null && ref.getSections()!=null) {
				Boolean isFunction = isFunction(ref.getId().getName());
				if(isFunction!=null && isFunction) {
					// replace data reference with function call
					//System.err.println(ref.getName()+" -- ");
					FunctionCall call = new FunctionCall(ref);
					return call;
				}
			}
		}
		return expr;
	}

	public Statement visit(Statement stmt) {
		return stmt;
	}
}
