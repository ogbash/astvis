/**
 * 
 */
package ee.olegus.fortran.ast;

import ee.olegus.fortran.ASTVisitor;
import java.util.List;
import java.util.ArrayList;

/**
 * @author olegus
 *
 */
public class CommonStatement extends Declaration {

	private List<CommonBlock> blocks=new ArrayList(2);

	/* (non-Javadoc)
	 * @see ee.olegus.fortran.ASTVisitable#astWalk(ee.olegus.fortran.ASTVisitor)
	 */
	public Object astWalk(ASTVisitor visitor) {
		// TODO Auto-generated method stub
		return this;
	}

	public final void addBlock(CommonBlock block) {
		blocks.add(block);
	}

}
