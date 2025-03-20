<?php
    header("Content-type: application/json");
    $local = "localhost";
    $user = "root";
    $senha = "";
    $banco = "loja";

    if( isset( $_REQUEST["buscar"] )){
        try{
            $conn = mysqli_connect($local, $user, $senha, $banco);
            if( $conn ){
                $query = "SELECT * FROM produto ORDER BY nome";
                $result = mysqli_query( $conn , $query );
                $linhas = array();
                while( $row = mysqli_fetch_assoc( $result ) ){
                    $linhas[] = $row;
                }
                mysqli_close( $conn );
                echo ' { "produtos" : '.json_encode($linhas).'  } ';
            }else{
                // Mensagem de erro
                echo ' { "resposta" : "Erro ao conectar ao banco"  } ';
            }
        }catch( \Throwable $th){
            // Mensagem de erro
            echo ' { "resposta" : "Erro no servidor"  } ';
        } 
    }

    if( isset( $_REQUEST["inserir"] )){
    	try{
        	$conn = mysqli_connect($local, $user, $senha, $banco);
        	if( $conn ){
 
            	$nome = $_POST["name"];
            	$preco = $_POST["price"];
 
            	$query = "INSERT INTO produto ( nome , preco ) VALUES ( '$nome' , $preco ) ";
                $query = "SELECT * FROM produto ORDER BY id";  // Ordena por id (ordem de inserção)

 
            	mysqli_query( $conn , $query );
            	$id = mysqli_insert_id( $conn );
                
            	mysqli_close( $conn );
                
            	echo ' { "id" : '.$id.'  } ';
 
        	}else{
            	// Mensagem de erro
            	echo ' { "resposta" : "Erro ao conectar ao banco"  } ';
        	}
    	}catch( \Throwable $th){
        	// Mensagem de erro
        	echo ' { "resposta" : "Erro no servidor"  } ';
    	}
	}
    if( isset( $_REQUEST["excluir"] ) && isset( $_POST["id"] )) {
        try {
            $conn = mysqli_connect($local, $user, $senha, $banco);
            if( $conn ) {
                $id = intval($_POST["id"]);  // Use o valor de $_POST['id'] e garanta que seja um número
                $query = "DELETE FROM produto WHERE id = $id";
    
                if (mysqli_query($conn, $query)) {
                    mysqli_close($conn);
                    echo ' { "resposta" : "Produto excluído com sucesso!" } ';
                } else {
                    echo ' { "resposta" : "Erro ao excluir o produto!" } ';
                }
            } else {
                echo ' { "resposta" : "Erro ao conectar ao banco"  } ';
            }
        } catch( \Throwable $th ) {
            echo ' { "resposta" : "Erro no servidor"  } ';
        }
    }
    
