package water.api;

import water.Key;
import water.api.ParseHandler.Parse;
import water.parser.ParserType;
import water.util.DocGen.HTML;

import java.util.Arrays;

public class ParseV2 extends Schema<Parse,ParseV2> {

  // Input fields
  @API(help="Final hex key name",required=true)
  Key hex;

  @API(help="Source keys",required=true)
  Key[] srcs;

  @API(help="Parser Type", values = {"AUTO", "ARFF", "XLS", "XLSX", "CSV", "SVMLight"})
  ParserType pType;

  @API(help="separator")
  byte sep;

  @API(help="ncols")
  int ncols;

  @API(help="Check header: 0 means guess, +1 means 1st line is header not data, -1 means 1st line is data not header")
  int checkHeader;

  @API(help="single Quotes")
  boolean singleQuotes;

  @API(help="Column Names")
  String[] columnNames;

  @API(help="Delete input key after parse")
  boolean delete_on_done;

  @API(help="Block until the parse completes (as opposed to returning early and requiring polling")
  boolean blocking;

  // Output fields
  @API(help="Job Key", direction=API.Direction.OUTPUT)
  Key job;

  //==========================

  @Override public HTML writeHTML_impl( HTML ab ) {
    ab.title("Parse Started");
    String url = JobV2.link(job);
    return ab.href("Poll",url,url);
  }

  // Helper so ParseSetup can link to Parse
  public static String link(Key[] srcs, String hexName, ParserType pType, byte sep, int ncols, int checkHeader, boolean singleQuotes, String[] columnNames) {
    return "Parse?srcs="+Arrays.toString(srcs)+
      "&hex="+hexName+
      "&pType="+pType+
      "&sep="+sep+
      "&ncols="+ncols+
      "&checkHeader="+checkHeader+
      "&singleQuotes="+singleQuotes+
      "&columnNames="+Arrays.toString(columnNames)+
      "";
  }
}
