

  -- clock process for generating 100 MHz clock
  clk_process :process
  begin
    clk1 <= '0';
    wait for clk1_period/2;
    clk1 <= '1';
    wait for clk1_period/2;
  end process;


