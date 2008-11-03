/**
 * 
 */
package ee.olegus.fortran.parser;

import java.util.Stack;

/**
 * Contains help constructs for parsing.
 * 
 * @author olegus
 *
 */
public class ParserStack<T> extends Stack<T> {
	private static final long serialVersionUID = 1L;

	private Stack<Integer> marks = new Stack<Integer>();
	
	public int pushMark() {
		int size = this.size();
		marks.push(size);
		return size;
	}
	
	public int popMark() {
		return marks.pop();
	}

	public int peekMark() {
		return marks.peek();
	}
	
	public int markCount() {
		return marks.size();
	}
}
