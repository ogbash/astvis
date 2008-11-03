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
public class ProcedureStatement extends Statement {
	private List<String> names;
	private String module;

	public String getModule() {
		return module;
	}

	public void setModule(String module) {
		this.module = module;
	}

	public List<String> getNames() {
		return names;
	}

	public void setNames(List<String> names) {
		this.names = names;
	}

	@Override
	public String toString() {
		return "MODULE "+(module!=null?module+" ":"")+"PROCEDURE "+names;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
