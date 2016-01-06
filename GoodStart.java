class GoodStart{
  boolean start = true;
  boolean reallyGood = true;

  public static void main(String [] args){
    GoodStart gStart = new GoodStart();
    if(gStart.start && gStart.reallyGood){
      System.out.println("It is really a very good start!!");
    }
    else{
      System.out.println("It is a start ... , start = "+gStart.start+"reallyGood = "+gStart.reallyGood);
    }
  }
}
