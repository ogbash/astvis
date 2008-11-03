/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;

import ee.olegus.fortran.ASTVisitor;

/**
 * Executable statement.
 * 
 * @author olegus
 *
 */
public class Executable extends Statement {

	private Code code;
	// top level list of expressions, has no real meaning
	// just temporary hack to find function call
	private List<Expression> expressions = new ArrayList<Expression>(3);
	
	public Executable(CommonTree tree, Code code) {
		this.code = code;
		parseExpression(tree, code);
	}

	/**
	 * @deprecated use parser action
	 */
	private void parseExpression(CommonTree tree, Code code) {
		/*
		for(int i=0; i<tree.getChildCount(); i++) {
			CommonTree child = (CommonTree) tree.getChild(i);
			switch (child.getType()) {
			case FortranParser.T_IDENT:
				expressions.add(new Reference(child, code, this));
				break;
			case FortranParser.L2:
				parseExpression(child, code);
				break;
			}
		}*/
	}

	public Iterator<Expression> getExpressions() {
		return expressions.iterator();
	}

	public Code getCode() {
		return code;
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}
}
