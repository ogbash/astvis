/**
 * 
 */
package ee.olegus.fortran.ast;

import java.util.ArrayList;
import java.util.List;

import org.antlr.runtime.tree.CommonTree;

import ee.olegus.fortran.ASTVisitor;

/**
 * @author olegus
 *
 */
public class Reference extends Expression {
	
	private Expression resolvedReference;
	private String name;
	private List<Expression[]> sections;

	public String getName() {
		return name;
	}

	public List<Expression[]> getSections() {
		return sections;
	}

	/**
	 * Reference within code.
	 * @param tree
	 * @param code
	 * @param statement
	 */
	public Reference(CommonTree tree, Code code, Statement statement) {
		super(tree, code, statement);
		this.name = tree.getText();
		
		// TODO parse sections (arguments)
	}

	/**
		@deprecated handled in post parsing
	*/
	public Expression getResolvedReference() {
		if(resolvedReference == null) {
			Scope scope = getLocation().code;
			// TODO generate arguments from sections and use them
			List<Expression> arguments = new ArrayList<Expression>();
			TypeShape ref = scope.getVariableOrFunction(name, null, false);
			//if(ref instanceof Subprogram)
				//resolvedReference = new FunctionCall(this, arguments, (Subprogram) ref);
		}
		return resolvedReference;
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getDimensions()
	 */
	public int getDimensions() {
		return getResolvedReference().getDimensions();
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#getType()
	 */
	public Type getType() {
		return getResolvedReference().getType();
	}

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ast.TypeShape#hasAttribute(ee.olegus.fortran.ast.Attribute.Type)
	 */
	public boolean hasAttribute(ee.olegus.fortran.ast.Attribute.Type type) {
		return getResolvedReference().hasAttribute(type);
	}

	public Object astWalk(ASTVisitor visitor) {
		return visitor.visit(this);
	}

}
